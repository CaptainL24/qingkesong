import { useEffect, useMemo, useRef, useState } from "react";
import type { JSX } from "react";

type ExerciseStep = {
  title: string;
  cue: string;
  seconds: number;
  targetMotion: number;
};

const STEPS: ExerciseStep[] = [
  {
    title: "校准坐姿",
    cue: "坐直，肩膀放松，看向屏幕中央。",
    seconds: 10,
    targetMotion: 4
  },
  {
    title: "左右转头",
    cue: "慢慢看向左侧，再慢慢回到右侧。",
    seconds: 18,
    targetMotion: 18
  },
  {
    title: "点头放松",
    cue: "轻轻低头，再抬头回正，不要耸肩。",
    seconds: 16,
    targetMotion: 14
  },
  {
    title: "肩颈画圈",
    cue: "肩膀向后绕圈，动作小一点也可以。",
    seconds: 18,
    targetMotion: 20
  },
  {
    title: "深呼吸收尾",
    cue: "吸气四拍，呼气四拍，让脖子松下来。",
    seconds: 14,
    targetMotion: 6
  }
];

const SAMPLE_WIDTH = 80;
const SAMPLE_HEIGHT = 60;

export function ExerciseView(): JSX.Element {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const previousFrameRef = useRef<Uint8ClampedArray | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number | null>(null);
  const stepStartedAtRef = useRef(0);
  const stepIndexRef = useRef(0);
  const phaseRef = useRef<"intro" | "running" | "done" | "error">("intro");
  const motionHitsRef = useRef(0);
  const totalScoreRef = useRef(0);
  const completedRef = useRef(false);
  const [phase, setPhase] = useState<"intro" | "running" | "done" | "error">("intro");
  const [stepIndex, setStepIndex] = useState(0);
  const [stepProgress, setStepProgress] = useState(0);
  const [motionScore, setMotionScore] = useState(0);
  const [totalScore, setTotalScore] = useState(0);
  const [error, setError] = useState("");

  const step = STEPS[stepIndex] ?? STEPS[0];
  const overallProgress = useMemo(() => {
    const completedSeconds = STEPS.slice(0, stepIndex).reduce((total, entry) => total + entry.seconds, 0);
    const totalSeconds = STEPS.reduce((total, entry) => total + entry.seconds, 0);
    return Math.min(100, Math.round(((completedSeconds + stepProgress * step.seconds) / totalSeconds) * 100));
  }, [step.seconds, stepIndex, stepProgress]);

  useEffect(() => {
    stepIndexRef.current = stepIndex;
  }, [stepIndex]);

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  useEffect(() => {
    totalScoreRef.current = totalScore;
  }, [totalScore]);

  useEffect(() => {
    return () => {
      if (rafRef.current !== null) window.cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function start(): Promise<void> {
    try {
      completedRef.current = false;
      previousFrameRef.current = null;
      motionHitsRef.current = 0;
      stepIndexRef.current = 0;
      setStepIndex(0);
      setStepProgress(0);
      setMotionScore(0);
      setTotalScore(0);
      totalScoreRef.current = 0;
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          width: { ideal: 960 },
          height: { ideal: 540 },
          facingMode: "user"
        }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      stepStartedAtRef.current = performance.now();
      setPhase("running");
      phaseRef.current = "running";
      rafRef.current = window.requestAnimationFrame(tick);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setPhase("error");
      phaseRef.current = "error";
    }
  }

  function finish(): void {
    if (completedRef.current) return;
    completedRef.current = true;
    if (rafRef.current !== null) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setPhase("done");
    phaseRef.current = "done";
    window.pawpause?.exerciseComplete(totalScoreRef.current);
  }

  function advanceStep(now: number): void {
    const nextScore = totalScoreRef.current + Math.min(25, Math.round(motionHitsRef.current / 3));
    totalScoreRef.current = nextScore;
    setTotalScore(nextScore);
    motionHitsRef.current = 0;
    previousFrameRef.current = null;
    setMotionScore(0);
    setStepProgress(0);
    stepStartedAtRef.current = now;
    const next = stepIndexRef.current + 1;
    if (next >= STEPS.length) {
      window.setTimeout(finish, 0);
      return;
    }
    stepIndexRef.current = next;
    setStepIndex(next);
  }

  function tick(now: number): void {
    if (phaseRef.current !== "running" || !videoRef.current?.srcObject) return;
    const currentStep = STEPS[stepIndexRef.current] ?? STEPS[0];
    const elapsedSeconds = (now - stepStartedAtRef.current) / 1000;
    const nextProgress = Math.min(1, elapsedSeconds / currentStep.seconds);
    setStepProgress(nextProgress);

    const score = sampleMotion();
    setMotionScore(score);
    if (score > currentStep.targetMotion) {
      motionHitsRef.current += 1;
    }

    if (nextProgress >= 1) {
      advanceStep(now);
    }
    rafRef.current = window.requestAnimationFrame(tick);
  }

  function sampleMotion(): number {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return 0;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return 0;
    canvas.width = SAMPLE_WIDTH;
    canvas.height = SAMPLE_HEIGHT;
    context.drawImage(video, 0, 0, SAMPLE_WIDTH, SAMPLE_HEIGHT);
    const data = context.getImageData(0, 0, SAMPLE_WIDTH, SAMPLE_HEIGHT).data;
    const previous = previousFrameRef.current;
    const current = new Uint8ClampedArray(SAMPLE_WIDTH * SAMPLE_HEIGHT);
    let diff = 0;

    for (let source = 0, target = 0; source < data.length; source += 4, target += 1) {
      const gray = Math.round(data[source] * 0.299 + data[source + 1] * 0.587 + data[source + 2] * 0.114);
      current[target] = gray;
      if (previous) diff += Math.abs(gray - previous[target]);
    }

    previousFrameRef.current = current;
    if (!previous) return 0;
    return Math.round(diff / current.length);
  }

  return (
    <main className="exercise-shell">
      <section className="exercise-stage">
        <video ref={videoRef} className="exercise-video" muted playsInline />
        <canvas ref={canvasRef} className="exercise-sampler" aria-hidden="true" />
        <div className="exercise-overlay">
          <div className="exercise-progress" aria-label="exercise progress">
            <span style={{ width: `${overallProgress}%` }} />
          </div>
          <div className="exercise-target">
            <span className="exercise-target__ring" />
            <span className="exercise-target__dot" />
          </div>
          <div className="exercise-readout">
            <span>运动感应</span>
            <strong>{motionScore}</strong>
          </div>
        </div>
      </section>

      <aside className="exercise-panel">
        <p className="exercise-kicker">PawPause 颈椎操</p>
        {phase === "intro" ? (
          <>
            <h1>用一分钟把班味抖掉</h1>
            <p>点击开始后才会打开摄像头。画面只在本地窗口里用来计算运动量，不会上传。</p>
            <button type="button" className="exercise-primary" onClick={() => void start()}>
              开始互动
            </button>
          </>
        ) : null}

        {phase === "running" ? (
          <>
            <span className="exercise-step-count">
              {stepIndex + 1}/{STEPS.length}
            </span>
            <h1>{step.title}</h1>
            <p>{step.cue}</p>
            <div className="exercise-meter">
              <span style={{ width: `${Math.round(stepProgress * 100)}%` }} />
            </div>
            <div className="exercise-stats">
              <div>
                <span>活力</span>
                <strong>{totalScore}</strong>
              </div>
              <div>
                <span>当前动作</span>
                <strong>{motionHitsRef.current}</strong>
              </div>
            </div>
            <button type="button" className="exercise-secondary" onClick={finish}>
              提前完成
            </button>
          </>
        ) : null}

        {phase === "done" ? (
          <>
            <h1>完成了，肩颈回魂一点点</h1>
            <p>桌宠已经收到完成反馈。下一版可以把这次动作结果写回你的健康数据链路。</p>
            <button type="button" className="exercise-primary" onClick={() => void start()}>
              再来一轮
            </button>
          </>
        ) : null}

        {phase === "error" ? (
          <>
            <h1>摄像头没有打开</h1>
            <p>{error || "请检查系统摄像头权限，然后再试一次。"}</p>
            <button type="button" className="exercise-primary" onClick={() => void start()}>
              重试
            </button>
          </>
        ) : null}
      </aside>
    </main>
  );
}
