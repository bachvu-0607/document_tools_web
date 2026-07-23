"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { checkOmrAlignment, uploadOmrSheet } from "@/lib/api";
import type { OmrSheetResponse } from "@/types/omr";

const CHECK_INTERVAL_MS = 300;
const PREVIEW_INTERVAL_MS = 120;
// Chi can 1 lan bao "du 4 goc" la chup ngay - da co man hinh xac nhan (xem
// pendingCapture ben duoi) de nguoi dung tu kiem tra/chup lai neu anh bi rung/
// mo, nen khong can giu yen nhieu lan lien tiep truoc khi chup nhu truoc nua.
const STABLE_CHECKS_REQUIRED = 1;

type Rotation = 0 | 90 | 180 | 270;

type OmrCameraCaptureProps = {
  onCaptured: (sheet: OmrSheetResponse) => void;
};

// Ve 1 khung hinh tu <video> vao canvas, co xoay theo goc chi dinh - dung
// CHUNG cho ca xem truoc, kiem tra can chinh, va chup that, de anh chup ra
// luon dung huong nhu nguoi dung da tu xoay tren khung xem truoc (khong con
// phai doan huong 90/180/270 nao la dung).
function drawRotatedFrame(video: HTMLVideoElement, rotation: Rotation, canvas: HTMLCanvasElement) {
  const swap = rotation === 90 || rotation === 270;
  const w = video.videoWidth;
  const h = video.videoHeight;
  canvas.width = swap ? h : w;
  canvas.height = swap ? w : h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.save();
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate((rotation * Math.PI) / 180);
  ctx.drawImage(video, -w / 2, -h / 2);
  ctx.restore();
}

export function OmrCameraCapture({ onCaptured }: OmrCameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const previewCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const stableCountRef = useRef(0);
  const busyRef = useRef(false);
  const waitingForRemovalRef = useRef(false);
  const rotationRef = useRef<Rotation>(0);

  const [activeStream, setActiveStream] = useState<MediaStream | null>(null);
  const [rotation, setRotation] = useState<Rotation>(0);
  const [aligned, setAligned] = useState(false);
  const [waitingForRemoval, setWaitingForRemoval] = useState(false);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState("");
  const [capturedCount, setCapturedCount] = useState(0);
  const [lastMessage, setLastMessage] = useState("");
  const [error, setError] = useState("");
  // Anh vua tu dong chup, CHUA tai len - cho nguoi chup xem lai va bam "Dong
  // y" truoc khi thuc su dung, tranh truong hop chup xong tai len/cham luon
  // ma nguoi chup chua kip biet minh vua chup duoc gi.
  const [pendingCapture, setPendingCapture] = useState<{ blob: Blob; previewUrl: string } | null>(null);
  const [uploadingCapture, setUploadingCapture] = useState(false);

  const streaming = activeStream !== null;

  useEffect(() => {
    rotationRef.current = rotation;
  }, [rotation]);

  // Video that chi dung lam "nguon khung hinh" (khong hien thi truc tiep) -
  // man hinh nguoi dung nhin la 1 canvas duoc ve lai lien tuc co ap dung goc
  // xoay, de xem truoc dung HUONG THAT se duoc chup (khong phai huong tho cua
  // camera).
  useEffect(() => {
    if (videoRef.current && activeStream) {
      videoRef.current.srcObject = activeStream;
    }
  }, [activeStream]);

  function stopStream() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setActiveStream(null);
    setAligned(false);
    stableCountRef.current = 0;
    waitingForRemovalRef.current = false;
    setWaitingForRemoval(false);
    busyRef.current = false;
    setPendingCapture((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return null;
    });
  }

  async function refreshDeviceList() {
    try {
      const list = await navigator.mediaDevices.enumerateDevices();
      setDevices(list.filter((d) => d.kind === "videoinput"));
    } catch {
      // Bo qua - danh sach cu van con dung duoc, khong chan luong chinh.
    }
  }

  async function startStream(deviceId?: string) {
    setError("");
    try {
      stopStream();
      // Lan mo dau tien: KHONG ep facingMode "environment" - de he dieu hanh
      // tu quyet dinh camera mac dinh (co the anh huong toi viec Continuity
      // Camera co duoc uu tien hay khong). Muon dung dung camera nao thi chon
      // lai tu danh sach ben duoi sau khi da mo.
      // LUON xin do phan giai cao (ideal, khong phai exact/min) - mac dinh
      // trinh duyet hay tra ve 640x480 qua thap, khong du chi tiet de nhan
      // dien dau goc/o tron chinh xac. "ideal" se tu lui ve muc camera ho tro
      // duoc neu khong dat toi 4K, khong lam getUserMedia that bai.
      const resolution = { width: { ideal: 3840 }, height: { ideal: 3840 } };
      const constraints: MediaStreamConstraints = {
        video: deviceId ? { deviceId: { exact: deviceId }, ...resolution } : resolution,
      };
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        // Mot so camera/trinh duyet tu choi thang ca yeu cau "ideal" - thu lai
        // voi rang buoc nhe hon (bo ep hinh VUONG 3840x3840, doi sang ty le
        // 16:9 thuong gap hon) nhung VAN xin do phan giai cao, tranh truong
        // hop rot xuong "video: true" khong rang buoc gi khien trinh duyet tu
        // chon muc mac dinh rat thap (anh mo, thieu chi tiet de doc o tron).
        if (err instanceof OverconstrainedError) {
          const fallbackResolution = { width: { ideal: 3840 }, height: { ideal: 2160 } };
          const fallback: MediaStreamConstraints = {
            video: deviceId ? { deviceId: { exact: deviceId }, ...fallbackResolution } : fallbackResolution,
          };
          stream = await navigator.mediaDevices.getUserMedia(fallback);
        } else {
          throw err;
        }
      }
      streamRef.current = stream;
      setActiveStream(stream);
      setRotation(0);

      // Ten camera chi hien day du SAU khi da co quyen - liet ke lai luc nay
      // de nguoi dung doi sang camera khac neu may co nhieu camera (vd iPhone
      // qua Continuity Camera se hien nhu 1 lua chon rieng).
      await refreshDeviceList();
      const activeTrackSettings = stream.getVideoTracks()[0]?.getSettings();
      if (activeTrackSettings?.deviceId) {
        setSelectedDeviceId(activeTrackSettings.deviceId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không mở được camera");
    }
  }

  function rotate90() {
    setRotation((prev) => ((prev + 90) % 360) as Rotation);
  }

  useEffect(() => {
    return () => stopStream();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Vong lap ve lai canvas xem truoc (~8 khung hinh/giay - du muot de canh
  // chinh, nhe hon nhieu so voi ve lai theo toc do that cua camera).
  useEffect(() => {
    if (!streaming) return;
    const timer = window.setInterval(() => {
      const video = videoRef.current;
      const canvas = previewCanvasRef.current;
      if (!video || !canvas || video.videoWidth === 0) return;
      drawRotatedFrame(video, rotationRef.current, canvas);
    }, PREVIEW_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [streaming]);

  useEffect(() => {
    if (!streaming) return;

    const timer = window.setInterval(async () => {
      if (busyRef.current || !videoRef.current) return;
      const video = videoRef.current;
      if (video.videoWidth === 0) return;

      // Anh nho, chat luong thap - chi de kiem tra nhanh co du 4 goc chua,
      // khong dung de chup that. Ve theo DUNG goc xoay hien tai, vi day chinh
      // la huong se duoc dung khi chup that.
      const fullRotated = document.createElement("canvas");
      drawRotatedFrame(video, rotationRef.current, fullRotated);
      const scale = 480 / fullRotated.width;
      const checkCanvas = document.createElement("canvas");
      checkCanvas.width = 480;
      checkCanvas.height = Math.round(fullRotated.height * scale);
      const ctx = checkCanvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(fullRotated, 0, 0, checkCanvas.width, checkCanvas.height);

      checkCanvas.toBlob(async (blob) => {
        if (!blob) return;
        const found = await checkOmrAlignment(blob);
        setAligned(found);

        if (!found) {
          // To giay da roi khoi khung (hoac chua dat vao) - san sang cho
          // luot chup tiep theo.
          waitingForRemovalRef.current = false;
          setWaitingForRemoval(false);
        }
        stableCountRef.current = found ? stableCountRef.current + 1 : 0;

        if (
          stableCountRef.current >= STABLE_CHECKS_REQUIRED &&
          !busyRef.current &&
          !waitingForRemovalRef.current
        ) {
          // busyRef GIU NGUYEN true (vong kiem tra tam dung) cho toi khi
          // nguoi dung bam "Dong y" hoac "Chup lai" - xem handleConfirmCapture/
          // handleRetakeCapture, khong tu dong tai len/cham ngay o day nua.
          busyRef.current = true;
          stableCountRef.current = 0;
          await handleAutoCapture(video);
        }
      }, "image/jpeg", 0.6);
    }, CHECK_INTERVAL_MS);

    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streaming]);

  async function handleAutoCapture(video: HTMLVideoElement) {
    const fullCanvas = document.createElement("canvas");
    drawRotatedFrame(video, rotationRef.current, fullCanvas);

    const blob: Blob | null = await new Promise((resolve) =>
      fullCanvas.toBlob(resolve, "image/jpeg", 0.92),
    );
    if (!blob) {
      busyRef.current = false;
      return;
    }
    setPendingCapture({ blob, previewUrl: URL.createObjectURL(blob) });
  }

  async function handleConfirmCapture() {
    if (!pendingCapture) return;
    setUploadingCapture(true);
    setError("");
    const filename = `camera-${new Date().toISOString().replace(/[:.]/g, "-")}.jpg`;
    const file = new File([pendingCapture.blob], filename, { type: "image/jpeg" });
    try {
      const result = await uploadOmrSheet(file, "");
      setCapturedCount((prev) => prev + 1);
      setLastMessage(`Đã tải lên: ${result.label}`);
      onCaptured(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tải ảnh lên thất bại");
    } finally {
      setUploadingCapture(false);
      URL.revokeObjectURL(pendingCapture.previewUrl);
      setPendingCapture(null);
      // Sau khi xac nhan, KHONG tu chup lai ngay du to giay van con canh dung
      // trong khung - cho toi khi nguoi dung dua to giay ra roi dua to tiep
      // theo vao thi moi chup lan nua. Tranh chup lien tuc nhieu lan cung 1 to.
      waitingForRemovalRef.current = true;
      setWaitingForRemoval(true);
      busyRef.current = false;
    }
  }

  function handleRetakeCapture() {
    setPendingCapture((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return null;
    });
    // Khong bat waitingForRemoval - cho phep tu dong chup lai ngay neu giay
    // van con dang canh dung trong khung, khong bat nguoi dung phai nhac ra.
    busyRef.current = false;
  }

  return (
    <div className="grid gap-3 rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
      {!streaming ? (
        <Button onClick={() => void startStream()} type="button" variant="secondary">
          📷 Mở camera
        </Button>
      ) : (
        <div className="grid gap-3">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video autoPlay className="hidden" muted playsInline ref={videoRef} />

          {pendingCapture ? (
            <div className="grid gap-3">
              <div className="relative overflow-hidden rounded-xl bg-black">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img alt="Ảnh vừa chụp — xem lại trước khi dùng" className="block w-full" src={pendingCapture.previewUrl} />
                <p className="absolute left-1/2 top-3 -translate-x-1/2 rounded-full bg-black/60 px-3 py-1 text-xs font-medium text-white">
                  Kiểm tra ảnh — rõ nét, đủ 4 góc chưa?
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  className="!min-h-11"
                  disabled={uploadingCapture}
                  onClick={handleRetakeCapture}
                  type="button"
                  variant="secondary"
                >
                  🔄 Chụp lại
                </Button>
                <Button className="!min-h-11" loading={uploadingCapture} onClick={() => void handleConfirmCapture()} type="button">
                  ✅ Đồng ý — dùng ảnh này
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="relative overflow-hidden rounded-xl bg-black">
                <canvas className="block w-full" ref={previewCanvasRef} />
                <div
                  className={`pointer-events-none absolute inset-6 rounded-xl border-4 transition-colors ${
                    waitingForRemoval ? "border-sky-400" : aligned ? "border-emerald-400" : "border-white/70"
                  }`}
                />
                <p
                  className={`absolute left-1/2 top-3 -translate-x-1/2 rounded-full px-3 py-1 text-xs font-medium text-white ${
                    waitingForRemoval ? "bg-sky-600" : aligned ? "bg-emerald-600" : "bg-black/60"
                  }`}
                >
                  {waitingForRemoval
                    ? "Đã chụp — nhấc phiếu ra rồi đặt phiếu tiếp theo vào"
                    : aligned
                      ? "Đã canh đúng — chuẩn bị chụp..."
                      : "Di chuyển máy để khớp 4 góc phiếu vào khung"}
                </p>
              </div>

              <div className="flex items-center justify-between gap-2">
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Nếu ảnh xem trước bị nghiêng/nằm ngang sai chiều, bấm xoay tới khi thấy đúng chiều đọc.
                </p>
                <Button className="!min-h-9 !px-3 !text-xs shrink-0" onClick={rotate90} type="button" variant="secondary">
                  ⟳ Xoay 90° ({rotation}°)
                </Button>
              </div>
            </>
          )}

          <div className="flex items-end gap-2">
            <label className="grid flex-1 gap-1 text-xs font-medium">
              Chọn camera ({devices.length} tìm thấy)
              <select
                className="min-h-9 rounded-lg border border-zinc-300 bg-white px-2 text-sm outline-none dark:border-zinc-700 dark:bg-zinc-900"
                onChange={(event) => void startStream(event.target.value)}
                value={selectedDeviceId}
              >
                {devices.map((device) => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label || "Camera"}
                  </option>
                ))}
              </select>
            </label>
            <Button
              className="!min-h-9 !px-3 !text-xs"
              onClick={() => void refreshDeviceList()}
              type="button"
              variant="secondary"
            >
              🔄 Làm mới
            </Button>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Không thấy camera iPhone (Continuity Camera)? Kiểm tra iPhone đang mở khoá, ở gần máy, cùng Wi-Fi/Bluetooth và cùng Apple ID, rồi bấm "Làm mới". Continuity Camera hoạt động ổn định nhất trên Safari.
          </p>

          <div className="flex items-center justify-between">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Đã tự động chụp: {capturedCount} ảnh</p>
            <Button onClick={stopStream} type="button" variant="secondary">
              Đóng camera
            </Button>
          </div>

          {lastMessage ? <p className="text-sm text-emerald-600 dark:text-emerald-400">{lastMessage}</p> : null}
        </div>
      )}

      {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
    </div>
  );
}
