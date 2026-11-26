#!/usr/bin/env bash
# reel.sh — the house edit, as code. Every command writes a NEW file; your source is never touched.
# Needs ffmpeg built with libass + freetype + fontconfig. On a Mac: brew install ffmpeg-full
# Fonts (fonts.google.com): Anton, Montserrat, Inter.
#
#   ./reel.sh check                                   # is this computer ready? (run first)
#   ./reel.sh reframe   in.mp4 out.mp4                # any ratio -> 1080x1920, center crop
#   ./reel.sh blurfill  in.mp4 out.mp4                # wide shot -> 9:16 with blurred fill, nothing cropped
#   ./reel.sh grade     in.mp4 out.mp4                # house warm/clean grade
#   ./reel.sh loudness  in.mp4 out.mp4                # voice to -14 LUFS, -1 dBTP
#   ./reel.sh hook      in.mp4 out.mp4 "TEXT" [sec=2.5]       # Anton hook, top third, centered lines
#   ./reel.sh punch     in.mp4 out.mp4 START END [zoom=1.10]  # centered punch-in with 6-frame ease
#   ./reel.sh captions  in.mp4 out.mp4 captions.srt           # house captions (see srt2ass.py)
#   ./reel.sh music     in.mp4 out.mp4 music.mp3              # music levelled, ducked under voice
#   ./reel.sh endcard   in.mp4 out.mp4 "CTA" "@handle"        # ADDS a 1.5s plum end card after the video
#   ./reel.sh export    in.mp4 out.mp4                # IG/TikTok upload spec
#   ./reel.sh all       in.mp4 out.mp4 "HOOK" [captions.srt]  # reframe+grade+hook+captions+loudness+export
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
W=1080; H=1920; FPS=30
GRADE="eq=contrast=1.06:saturation=1.08:gamma=1.02,colorbalance=rs=0.03:bs=-0.03:rm=0.02:bm=-0.02"
INK="0x1A1220"; CREAM="0xF6F0E8"; PLUM="0x4A1F3D"; GOLD="0xC9A24A"
ENC=(-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart)
AUD=(-c:a aac -b:a 192k -ar 48000)
TMP="$(mktemp -d "${TMPDIR:-/tmp}/reel.XXXXXX")"; trap 'rm -rf "$TMP"' EXIT

die(){ echo "error: $*" >&2; exit 1; }
need(){ [ "$1" -ge "$2" ] || die "missing arguments. Run: $0 help"; }
has_audio(){ ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1" | grep -q .; }
filters_ok(){ local l; l="$(ffmpeg -hide_banner -filters 2>/dev/null || true)"; printf '%s\n' "$l" | grep -E "^ .{3} $1 " >/dev/null; }
need_text(){ filters_ok drawtext && filters_ok ass && command -v fc-match >/dev/null \
  || die "your ffmpeg can't draw text. Mac: brew uninstall ffmpeg && brew install ffmpeg-full   (Linux: apt install ffmpeg fontconfig)"; }
font(){ # path to font file; warns when the brand font is missing
  local fam; fam="$(fc-match -f '%{family}' "$1" 2>/dev/null || true)"
  case "$fam" in *"$1"*) ;; *) echo "warning: font '$1' not installed, using '$fam'. Install it from fonts.google.com." >&2;; esac
  fc-match -f '%{file}' "$1"; }
# escape a path for use inside '...' in an ffmpeg filter argument
q(){ printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e "s/'/'\\\\''/g" -e 's/:/\\:/g'; }
# centered multi-line text, one drawtext per line. args: fontfile size color border y0 lineheight enable textfile
lines_filter(){
  local f="$1" size="$2" color="$3" border="$4" y="$5" lh="$6" en="$7" src="$8" i=0 out="" lf line
  while IFS= read -r line || [ -n "$line" ]; do
    lf="$TMP/line$RANDOM$i.txt"; printf '%s' "$line" > "$lf"
    out="$out${out:+,}drawtext=fontfile='$(q "$f")':textfile='$(q "$lf")':expansion=none:fontsize=$size:fontcolor=$color:borderw=$border:bordercolor=$INK:x=(w-text_w)/2:y=$((y + i*lh)):enable='$en'"
    i=$((i+1))
  done < "$src"
  printf '%s' "$out"; }

cmd="${1:-help}"; shift || true
case "$cmd" in
  check)
    command -v ffmpeg >/dev/null || die "ffmpeg not installed. Mac: brew install ffmpeg-full"
    need_text; for f in Anton Montserrat Inter; do font "$f" >/dev/null; done
    echo "ready: $(ffmpeg -version | head -1)" ;;

  reframe) need $# 2
    ffmpeg -y -i "$1" -vf "scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,setsar=1,fps=$FPS" "${ENC[@]}" -c:a copy "$2" ;;

  blurfill) need $# 2
    ffmpeg -y -i "$1" -filter_complex \
      "[0:v]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,boxblur=30:3,eq=brightness=-0.08[bg];[0:v]scale=$W:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=$FPS" \
      "${ENC[@]}" -c:a copy "$2" ;;

  grade) need $# 2
    ffmpeg -y -i "$1" -vf "$GRADE" "${ENC[@]}" -c:a copy "$2" ;;

  loudness) need $# 2
    has_audio "$1" || die "no audio track in $1"
    ffmpeg -y -i "$1" -af "highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1:LRA=9" -c:v copy "${AUD[@]}" "$2" ;;

  hook) need $# 3; need_text
    T="${4:-2.5}"; F="$(font Anton)"
    printf '%s\n' "$3" | tr '[:lower:]' '[:upper:]' | fold -s -w 16 | sed 's/ *$//' > "$TMP/hook.txt"
    ffmpeg -y -i "$1" -vf "$(lines_filter "$F" 96 white 8 300 116 "between(t,0,$T)" "$TMP/hook.txt")" "${ENC[@]}" -c:a copy "$2" ;;

  punch) need $# 4
    Z="${5:-1.10}"
    awk -v z="$Z" 'BEGIN{exit !(z>=1 && z<=2)}' || die "zoom must be between 1.0 and 2.0"
    # ease-in over 6 frames (0.2s), zoom stays centered
    ffmpeg -y -i "$1" -vf "scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,fps=$FPS,\
zoompan=z='if(between(it,$3,$4),min($Z,1+(it-$3)*($Z-1)*5),1)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=${W}x${H}:fps=$FPS,setsar=1" \
      "${ENC[@]}" -c:a copy "$2" ;;

  captions) need $# 3; need_text
    font Montserrat >/dev/null
    python3 "$HERE/srt2ass.py" "$3" "$TMP/c.ass"
    ffmpeg -y -i "$1" -vf "ass='$(q "$TMP/c.ass")'" "${ENC[@]}" -c:a copy "$2" ;;

  music) need $# 3
    has_audio "$1" || die "no voice track in $1"
    # music levelled to -32 LUFS (about 18 dB under a -14 LUFS voice), looped, then ducked further while you talk
    ffmpeg -y -i "$1" -stream_loop -1 -i "$3" -filter_complex \
      "[1:a]loudnorm=I=-32:TP=-6,aresample=48000[m];[0:a]aresample=48000,asplit[v][sc];\
[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];[v][duck]amix=inputs=2:duration=first:normalize=0[a]" \
      -map 0:v -map "[a]" -c:v copy "${AUD[@]}" "$2" ;;

  endcard) need $# 4; need_text
    F="$(font Anton)"; B="$(font Inter)"
    printf '%s\n' "$3" | tr '[:lower:]' '[:upper:]' | fold -s -w 14 | sed 's/ *$//' > "$TMP/cta.txt"
    printf '%s\n' "$4" > "$TMP/handle.txt"
    N=$(wc -l < "$TMP/cta.txt" | tr -d ' '); Y0=$((800 - N*60)); HY=$((Y0 + N*124 + 40))
    if has_audio "$1"; then SIL=(-f lavfi -i "anullsrc=r=48000:cl=stereo"); AMAP=(-map 1:a); CA=("${AUD[@]}"); else SIL=(); AMAP=(); CA=(-an); fi
    ffmpeg -y -f lavfi -i "color=c=$PLUM:s=${W}x${H}:r=$FPS:d=1.5" ${SIL[@]+"${SIL[@]}"} -vf \
      "$(lines_filter "$F" 110 "$CREAM" 0 "$Y0" 124 1 "$TMP/cta.txt"),$(lines_filter "$B" 52 "$GOLD" 0 "$HY" 60 1 "$TMP/handle.txt"),\
drawbox=x=(iw-360)/2:y=$((HY+72)):w=360:h=6:color=$GOLD:t=fill,format=yuv420p" \
      -map 0:v ${AMAP[@]+"${AMAP[@]}"} -t 1.5 "${ENC[@]}" "${CA[@]}" "$TMP/card.mp4"
    "$0" export "$1" "$TMP/main.mp4" >/dev/null 2>&1
    if has_audio "$1"; then
      ffmpeg -y -i "$TMP/main.mp4" -i "$TMP/card.mp4" -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" "${ENC[@]}" "${AUD[@]}" "$2"
    else
      ffmpeg -y -i "$TMP/main.mp4" -i "$TMP/card.mp4" -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" "${ENC[@]}" "$2"
    fi ;;

  export) need $# 2
    if has_audio "$1"; then A=("${AUD[@]}"); else A=(-an); fi
    ffmpeg -y -i "$1" -vf "scale=$W:$H:force_original_aspect_ratio=decrease,pad=$W:$H:(ow-iw)/2:(oh-ih)/2:color=$INK,fps=$FPS,setsar=1" \
      -c:v libx264 -profile:v high -level 4.1 -preset slow -crf 18 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -movflags +faststart "${A[@]}" "$2" ;;

  all) need $# 3
    "$0" reframe "$1" "$TMP/1.mp4"
    "$0" grade   "$TMP/1.mp4" "$TMP/2.mp4"
    "$0" hook    "$TMP/2.mp4" "$TMP/3.mp4" "$3"
    CUR="$TMP/3.mp4"
    if [ -n "${4:-}" ]; then "$0" captions "$CUR" "$TMP/4.mp4" "$4"; CUR="$TMP/4.mp4"; fi
    if has_audio "$CUR"; then "$0" loudness "$CUR" "$TMP/5.mp4"; CUR="$TMP/5.mp4"; fi
    "$0" export "$CUR" "$2" ;;

  *) sed -n '2,17p' "$0" ;;
esac
