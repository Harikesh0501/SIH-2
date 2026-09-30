"use client";
/* eslint-disable @next/next/no-img-element */

import React, { useState } from "react";
import { QrCode } from "lucide-react";

interface QRCodeDisplayProps {
  value: string;
  dataUri?: string;
  size?: number;
  className?: string;
  alt?: string;
}

export function QRCodeDisplay({
  value,
  dataUri,
  size = 140,
  className = "",
  alt = "Verifiable QR Code"
}: QRCodeDisplayProps) {
  const [loadFailed, setLoadFailed] = useState(false);

  if (dataUri && !loadFailed) {
    return (
      <div
        className={`inline-flex items-center justify-center p-2 bg-white rounded border border-zinc-200 ${className}`}
        style={{ width: size + 16, height: size + 16 }}
      >
        <img src={dataUri} alt={alt} width={size} height={size} className="object-contain" onError={() => setLoadFailed(true)} />
      </div>
    );
  }

  const externalQrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size * 2}x${size * 2}&data=${encodeURIComponent(value)}&color=0-0-0&bgcolor=255-255-255&margin=1`;

  if (!loadFailed) {
    return (
      <div
        className={`inline-flex items-center justify-center p-2 bg-white rounded border border-zinc-200 ${className}`}
        style={{ width: size + 16, height: size + 16 }}
      >
        <img src={externalQrUrl} alt={alt} width={size} height={size} className="object-contain" onError={() => setLoadFailed(true)} />
      </div>
    );
  }

  return (
    <div
      className={`relative inline-flex flex-col items-center justify-center p-2 bg-white rounded border border-zinc-300 ${className}`}
      style={{ width: size + 16, height: size + 16 }}
    >
      <svg width={size} height={size} viewBox="0 0 100 100">
        <rect width="100" height="100" fill="#ffffff" />
        <rect x="5" y="5" width="28" height="28" fill="#09090b" rx="2" />
        <rect x="10" y="10" width="18" height="18" fill="#ffffff" rx="1" />
        <rect x="14" y="14" width="10" height="10" fill="#09090b" rx="1" />
        <rect x="67" y="5" width="28" height="28" fill="#09090b" rx="2" />
        <rect x="72" y="10" width="18" height="18" fill="#ffffff" rx="1" />
        <rect x="76" y="14" width="10" height="10" fill="#09090b" rx="1" />
        <rect x="5" y="67" width="28" height="28" fill="#09090b" rx="2" />
        <rect x="10" y="72" width="18" height="18" fill="#ffffff" rx="1" />
        <rect x="14" y="76" width="10" height="10" fill="#09090b" rx="1" />
        <rect x="38" y="10" width="6" height="6" fill="#09090b" />
        <rect x="48" y="10" width="6" height="6" fill="#09090b" />
        <rect x="40" y="40" width="20" height="20" fill="#09090b" rx="2" />
        <rect x="44" y="44" width="12" height="12" fill="#ffffff" rx="1" />
        <rect x="47" y="47" width="6" height="6" fill="#09090b" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-6 h-6 rounded bg-white border border-zinc-900 flex items-center justify-center">
          <QrCode className="w-3.5 h-3.5 text-zinc-900" />
        </div>
      </div>
    </div>
  );
}
