// Jani's reference looks (Nov 28 2026). Transparent 1080x1920 overlays for her own footage.
// Technique only: built fresh, nobody's footage, fonts or words copied.
// Any colour works (Jani, Nov 28: "I love red, pink, blue, green, all colors"). Bright colours get a shadow so they stay readable.
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Composition,
  Easing,
  Interactive,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";

const { fontFamily: anton } = loadAnton("normal", { weights: ["400"] });
const { fontFamily: playfair } = loadPlayfair("italic", { weights: ["500"] });

export const COLORS = {
  cream: "#F6EDE3",
  blush: "#E8B4B8",
  gold: "#E2B95C",
  plum: "#5B2A4E",
  teal: "#2F6F6B",
  lime: "#D7F24A",
  red: "#E5383B",
  pink: "#FF4FA3",
  blue: "#2F80ED",
  green: "#27AE60",
  white: "#FFFFFF",
  black: "#111111",
} as const;
type ColorName = keyof typeof COLORS;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const W = 1080;
const H = 1920;
const FPS = 30;

type WithDuration = { durationInSeconds: number };
function withDuration<T extends WithDuration>(): CalculateMetadataFunction<T> {
  return ({ props }) => ({
    durationInFrames: Math.max(1, Math.round(props.durationInSeconds * FPS)),
  });
}

/* ---------- 1. Reach & Pull: title drops on two gold strings when she "pulls" it down ---------- */
export type ReachPullProps = WithDuration & {
  title: string;
  dropAtSeconds: number; // the frame her fist closes
  topPx: number; // where the banner settles (keep >= 250 for the safe zone)
  textColor: ColorName;
  bannerColor: ColorName;
};

export const ReachPull: React.FC<ReachPullProps> = ({ title, dropAtSeconds, topPx, textColor, bannerColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - dropAtSeconds * fps;
  return (
    <AbsoluteFill>
      <Interactive.Div
        name="Banner"
        style={{
          position: "absolute",
          left: 90,
          right: 90,
          top: topPx,
          translate: interpolate(t, [0, 0.45 * fps], ["0px -900px", "0px 0px"], {
            ...clamp,
            easing: Easing.bezier(0.34, 1.56, 0.64, 1), // overshoot = the bounce
          }),
          rotate: interpolate(t, [0.3 * fps, 0.6 * fps, 0.9 * fps, 1.3 * fps], ["-4deg", "3deg", "-1.5deg", "0deg"], clamp),
          opacity: t < 0 ? 0 : 1,
          transformOrigin: "50% -400px",
        }}
      >
        {[18, 82].map((x) => (
          <div
            key={x}
            style={{
              position: "absolute",
              left: `${x}%`,
              bottom: "100%",
              width: 4,
              height: 2000,
              background: COLORS.gold,
              opacity: 0.9,
            }}
          />
        ))}
        <div
          style={{
            background: COLORS[bannerColor],
            borderRadius: 28,
            padding: "36px 40px",
            textAlign: "center",
            fontFamily: anton,
            fontSize: 104,
            lineHeight: 1.02,
            letterSpacing: 1,
            textTransform: "uppercase",
            color: COLORS[textColor],
            boxShadow: "0 18px 40px rgba(0,0,0,0.28)",
          }}
        >
          {title}
        </div>
      </Interactive.Div>
    </AbsoluteFill>
  );
};

/* ---------- 2. One-Word Truth: one lowercase italic serif word with a full stop, per beat ---------- */
export type TruthWord = { text: string; atSeconds: number; untilSeconds: number };
export type OneWordTruthProps = WithDuration & {
  words: TruthWord[];
  topPx: number; // put it where her head will cover part of it (layer it UNDER her cut-out)
  color: ColorName;
  sizePx: number;
};

const TruthBeat: React.FC<{ w: TruthWord; topPx: number; color: ColorName; sizePx: number }> = ({ w, topPx, color, sizePx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = w.atSeconds * fps;
  const b = w.untilSeconds * fps;
  return (
    <Interactive.Div
      name={`Word ${w.text}`}
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: topPx,
        textAlign: "center",
        fontFamily: playfair,
        fontStyle: "italic",
        fontWeight: 500,
        fontSize: sizePx,
        color: COLORS[color],
        textShadow: "0 6px 30px rgba(0,0,0,0.25)",
        opacity: interpolate(frame, [a, a + 8, b - 6, b], [0, 1, 1, 0], clamp),
        filter: `blur(${interpolate(frame, [a, a + 8], [14, 0], clamp)}px)`,
        translate: interpolate(frame, [a, b], ["0px 24px", "0px -12px"], clamp),
      }}
    >
      {w.text.toLowerCase().replace(/\.*$/, "")}.
    </Interactive.Div>
  );
};

export const OneWordTruth: React.FC<OneWordTruthProps> = ({ words, topPx, color, sizePx }) => (
  <AbsoluteFill>
    {words.map((w) => (
      <TruthBeat key={`${w.text}-${w.atSeconds}`} w={w} topPx={topPx} color={color} sizePx={sizePx} />
    ))}
  </AbsoluteFill>
);

/* ---------- 3. Bright Title: big bold headline + small white subline, pop-in ---------- */
export type BrightTitleProps = WithDuration & {
  title: string;
  subline: string;
  atSeconds: number;
  color: ColorName;
  topPx: number;
};

export const BrightTitle: React.FC<BrightTitleProps> = ({ title, subline, atSeconds, color, topPx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = atSeconds * fps;
  return (
    <AbsoluteFill>
      <Interactive.Div
        name="Title"
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          top: topPx,
          textAlign: "center",
          fontFamily: anton,
          fontSize: 120,
          lineHeight: 1,
          textTransform: "uppercase",
          color: COLORS[color],
          textShadow: "0 6px 24px rgba(0,0,0,0.35)",
          opacity: frame < a ? 0 : 1,
          scale: interpolate(frame, [a, a + 9], [0.7, 1], {
            ...clamp,
            easing: Easing.bezier(0.34, 1.56, 0.64, 1),
          }),
        }}
      >
        {title}
      </Interactive.Div>
      <Interactive.Div
        name="Subline"
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          top: topPx + 150,
          textAlign: "center",
          fontFamily: "Helvetica, Arial, sans-serif",
          fontWeight: 700,
          fontSize: 50,
          color: "white",
          textShadow: "0 4px 16px rgba(0,0,0,0.4)",
          opacity: interpolate(frame, [a + 6, a + 14], [0, 1], clamp),
          translate: interpolate(frame, [a + 6, a + 14], ["0px 16px", "0px 0px"], clamp),
        }}
      >
        {subline}
      </Interactive.Div>
    </AbsoluteFill>
  );
};

export const Looks: React.FC = () => (
  <>
    <Composition
      id="ReachPull"
      component={ReachPull}
      durationInFrames={120}
      fps={FPS}
      width={W}
      height={H}
      calculateMetadata={withDuration<ReachPullProps>()}
      defaultProps={{
        durationInSeconds: 4,
        title: "My heart is still soft",
        dropAtSeconds: 0.6,
        topPx: 300,
        textColor: "plum" as ColorName,
        bannerColor: "cream" as ColorName,
      }}
    />
    <Composition
      id="OneWordTruth"
      component={OneWordTruth}
      durationInFrames={180}
      fps={FPS}
      width={W}
      height={H}
      calculateMetadata={withDuration<OneWordTruthProps>()}
      defaultProps={{
        durationInSeconds: 6,
        topPx: 420,
        color: "cream" as ColorName,
        sizePx: 240,
        words: [
          { text: "why", atSeconds: 0.3, untilSeconds: 2.6 },
          { text: "worthy", atSeconds: 3, untilSeconds: 5.8 },
        ],
      }}
    />
    <Composition
      id="BrightTitle"
      component={BrightTitle}
      durationInFrames={120}
      fps={FPS}
      width={W}
      height={H}
      calculateMetadata={withDuration<BrightTitleProps>()}
      defaultProps={{
        durationInSeconds: 4,
        title: "3 rules for 2027",
        subline: "never break these",
        atSeconds: 0.2,
        color: "gold" as ColorName,
        topPx: 330,
      }}
    />
  </>
);
