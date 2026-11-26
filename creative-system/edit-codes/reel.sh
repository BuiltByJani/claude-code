#!/usr/bin/env bash
# reel.sh — the house edit, as code. Every command outputs a NEW file; your source is never touched.
# Needs: ffmpeg 5+ and the fonts in ../design-system/tokens.json (Montserrat, Anton) installed.
#
#   ./reel.sh reframe   in.mp4 out.mp4            # any ratio -> 1080x1920 9:16, center crop
#   ./reel.sh blurfill  in.mp4 out.mp4            # landscape -> 9:16 with blurred fill (no crop of the subject)
#   ./reel.sh grade     in.mp4 out.mp4            # house warm/clean grade
#   ./reel.sh loudness  in.mp4 out.mp4            # voice to -14 LUFS, -1 dBTP (IG/TikTok/Reels standard)
#   ./reel.sh hook      in.mp4 out.mp4 "TEXT" [seconds=2.5]   # Anton hook text, top-third, inside safe zone
#   ./reel.sh punch     in.mp4 out.mp4 START END [zoom=1.10]  # punch-in zoom on an emphasis moment
#   ./reel.sh captions  in.mp4 out.mp4 captions.srt           # burn house-style captions (see srt2ass.py)
#   ./reel.sh music     in.mp4 out.mp4 music.mp3              # duck music to -18 dB under voice
#   ./reel.sh endcard   in.mp4 out.mp4 "FOLLOW FOR PART 2" "@handle"
#   ./reel.sh export    in.mp4 out.mp4            # final IG/TikTok spec: H.264 high, 30fps, AAC 48k
#   ./reel.sh all       in.mp4 out.mp4 "HOOK TEXT" [captions.srt]  # reframe+grade+hook+captions+loudness+export
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
W=1080; H=1920; FPS=30
GRADE="eq=contrast=1.06:saturation=1.08:gamma=1.02,colorbalance=rs=0.03:bs=-0.03:rm=0.02:bm=-0.02"
INK="0x1A1220"; CREAM="0xF6F0E8"; PLUM="0x4A1F3D"; GOLD="0xC9A24A"
ENC=(-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart)
AUD=(-c:a aac -b:a 192k -ar 48000)

die(){ echo "error: $*" >&2; exit 1; }
need(){ [ "$#" -ge "$1" ] || die "missing arguments. Run: $0 help"; }
has_audio(){ ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1" | grep -q .; }
esc(){ printf '%s' "$1" | sed -e "s/\\\\/\\\\\\\\/g" -e "s/'/\\\\'/g" -e 's/:/\\:/g' -e 's/%/\\%/g'; }
font(){ local fam; fam="$(fc-match -f '%{family}' "$1" 2>/dev/null || true)"
  case "$fam" in *"$1"*) ;; *) echo "warning: font '$1' not installed, using '$fam'. Install it from fonts.google.com for the on-brand look." >&2;; esac
  fc-match -f '%{file}' "$1" 2>/dev/null || true; }

cmd="${1:-help}"; shift || true
case "$cmd" in
  reframe) need 2 "$@"
    ffmpeg -y -i "$1" -vf "scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,setsar=1,fps=$FPS" "${ENC[@]}" -c:a copy "$2" ;;

  blurfill) need 2 "$@"
    ffmpeg -y -i "$1" -filter_complex \
      "[0:v]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,boxblur=30:3,eq=brightness=-0.08[bg];\
       [0:v]scale=$W:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=$FPS" "${ENC[@]}" -c:a copy "$2" ;;

  grade) need 2 "$@"
    ffmpeg -y -i "$1" -vf "$GRADE" "${ENC[@]}" -c:a copy "$2" ;;

  loudness) need 2 "$@"
    has_audio "$1" || die "no audio track in $1"
    ffmpeg -y -i "$1" -af "highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1:LRA=9" -c:v copy "${AUD[@]}" "$2" ;;

  hook) need 3 "$@"
    T="${4:-2.5}"; F="$(font 'Anton')"
    TF="$(mktemp)"; printf '%s' "$3" | tr '[:lower:]' '[:upper:]' | fold -s -w 16 | sed 's/ *$//' > "$TF"
    ffmpeg -y -i "$1" -vf "drawtext=fontfile='$F':textfile='$TF':expansion=none:fontsize=96:fontcolor=white:borderw=8:bordercolor=$INK:line_spacing=10:\
x=(w-text_w)/2:y=300:enable='between(t,0,$T)':alpha='if(lt(t,0.13),t/0.13,1)'" "${ENC[@]}" -c:a copy "$2"; rm -f "$TF" ;;

  punch) need 4 "$@"
    Z="${5:-1.10}"
    ffmpeg -y -i "$1" -vf "scale=w='iw*if(between(t,$3,$4),$Z,1)':h='ih*if(between(t,$3,$4),$Z,1)':eval=frame,crop=$W:$H,setsar=1" "${ENC[@]}" -c:a copy "$2" ;;

  captions) need 3 "$@"
    ASS="${2%.*}.ass"; python3 "$HERE/srt2ass.py" "$3" "$ASS"
    ffmpeg -y -i "$1" -vf "ass='$(esc "$ASS")'" "${ENC[@]}" -c:a copy "$2" ;;

  music) need 3 "$@"
    has_audio "$1" || die "no voice track in $1"
    ffmpeg -y -i "$1" -stream_loop -1 -i "$3" -filter_complex \
      "[1:a]volume=-18dB[m];[m][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[duck];\
       [0:a][duck]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy "${AUD[@]}" -shortest "$2" ;;

  endcard) need 4 "$@"
    F="$(font 'Anton')"; B="$(font 'Inter')"
    D="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")"
    S="$(python3 -c "print(max(0,float('$D')-1.5))")"
    T1="$(mktemp)"; T2="$(mktemp)"; printf '%s' "$3" > "$T1"; printf '%s' "$4" > "$T2"
    ffmpeg -y -i "$1" -vf "drawbox=x=0:y=0:w=iw:h=ih:color=$PLUM:t=fill:enable='gte(t,$S)',\
drawtext=fontfile='$F':textfile='$T1':expansion=none:fontsize=110:fontcolor=$CREAM:x=(w-text_w)/2:y=(h-text_h)/2-60:enable='gte(t,$S)',\
drawtext=fontfile='$B':textfile='$T2':expansion=none:fontsize=52:fontcolor=$GOLD:x=(w-text_w)/2:y=(h/2)+90:enable='gte(t,$S)'" \
      "${ENC[@]}" -c:a copy "$2"; rm -f "$T1" "$T2" ;;

  export) need 2 "$@"
    if has_audio "$1"; then A=("${AUD[@]}"); else A=(-an); fi
    ffmpeg -y -i "$1" -vf "scale=$W:$H:force_original_aspect_ratio=decrease,pad=$W:$H:(ow-iw)/2:(oh-ih)/2:color=$INK,fps=$FPS,setsar=1" \
      -c:v libx264 -profile:v high -level 4.1 -preset slow -crf 18 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -movflags +faststart "${A[@]}" "$2" ;;

  all) need 3 "$@"
    TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
    "$0" reframe "$1" "$TMP/1.mp4"
    "$0" grade   "$TMP/1.mp4" "$TMP/2.mp4"
    "$0" hook    "$TMP/2.mp4" "$TMP/3.mp4" "$3"
    CUR="$TMP/3.mp4"
    if [ -n "${4:-}" ]; then "$0" captions "$CUR" "$TMP/4.mp4" "$4"; CUR="$TMP/4.mp4"; fi
    if has_audio "$CUR"; then "$0" loudness "$CUR" "$TMP/5.mp4"; CUR="$TMP/5.mp4"; fi
    "$0" export "$CUR" "$2" ;;

  *) sed -n '2,17p' "$0" ;;
esac
