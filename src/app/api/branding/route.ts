import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

function readEnv(key: string): string {
  // Check files on disk first so edits in VS Code (.env.example or .env) are immediately read
  const files = [".env.local", ".env", ".env.development", ".env.example"];
  for (const file of files) {
    try {
      const fullPath = path.join(process.cwd(), file);
      if (fs.existsSync(fullPath)) {
        const lines = fs.readFileSync(fullPath, "utf-8").split(/\r?\n/);
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("#") || !trimmed.includes("=")) continue;
          const [k, ...rest] = trimmed.split("=");
          if (k.trim() === key) {
            const val = rest.join("=").trim().replace(/^["']|["']$/g, "");
            if (val) return val;
          }
        }
      }
    } catch {
      // ignore
    }
  }

  // Fallback to cached process.env
  if (process.env[key] && process.env[key]!.trim() !== "") {
    return process.env[key]!.trim().replace(/^["']|["']$/g, "");
  }

  return "";
}

export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * GET /api/branding
 * Dynamically resolves the institution logo and name:
 * Reads INST_CODE_BGIMAGE (path or keyword) and explicit logo variables from env.
 */
export async function GET() {
  const instCodeBg =
    readEnv("NEXT_PUBLIC_INST_CODE_BGIMAGE") ||
    readEnv("INST_CODE_BGIMAGE") ||
    "";

  const rawLogo =
    readEnv("NEXT_PUBLIC_INSTITUTE_LOGO") ||
    readEnv("INSTITUTE_LOGO") ||
    readEnv("NEXT_PUBLIC_SCHOOL_LOGO") ||
    readEnv("SCHOOL_LOGO") ||
    "";

  const rawName =
    readEnv("NEXT_PUBLIC_INSTITUTE_NAME") ||
    readEnv("INSTITUTE_NAME") ||
    readEnv("NEXT_PUBLIC_SCHOOL_NAME") ||
    readEnv("SCHOOL_NAME") ||
    "";

  // Target can be a full URL, relative file path, or keyword (e.g. MVPS)
  const target = (rawLogo || instCodeBg).trim();

  let resolvedLogo = "";
  if (target) {
    if (/^(https?:|\/\/|data:)/i.test(target)) {
      resolvedLogo = target;
    } else if (target.includes("/") || target.includes("\\") || /\.(png|jpe?g|svg|webp|gif|ico)$/i.test(target)) {
      const norm = target.replace(/\\/g, "/");
      resolvedLogo = norm.startsWith("/") ? norm : `/${norm}`;
    } else {
      const upper = target.toUpperCase();
      const map: Record<string, string> = {
        MVPS: "/mvps/brand/logo.png",
        BDC: "/bdc/brand/logo.png",
        CAMPUS: "/campus/brand/logo.png",
      };
      resolvedLogo = map[upper] || `/${target.toLowerCase()}/brand/logo.png`;
    }
  }

  const resolvedName =
    rawName ||
    (instCodeBg && instCodeBg.toUpperCase() === "BDC"
      ? "BD Campus"
      : instCodeBg && instCodeBg.toUpperCase() === "MVPS"
        ? "Madhuvan Vatika - MVPS"
        : "Baldwin Boys High School");

  const rawCode =
    readEnv("NEXT_PUBLIC_INST_CODE") ||
    readEnv("INST_CODE") ||
    readEnv("INSTITUTE_CODE") ||
    "";

  let resolvedCode = rawCode.trim().toUpperCase();
  if (!resolvedCode) {
    if (resolvedName) {
      if (/balwin|baldwin/i.test(resolvedName)) resolvedCode = "BBHS";
      else if (/bd campus/i.test(resolvedName)) resolvedCode = "BDC";
      else if (/madhuvan/i.test(resolvedName)) resolvedCode = "MVPS";
      else {
        const words = resolvedName.replace(/[^a-zA-Z0-9\s]/g, "").trim().split(/\s+/);
        resolvedCode =
          words.length > 1 && words.length <= 4
            ? words.map((w: string) => w[0].toUpperCase()).join("")
            : "BBHS";
      }
    } else if (instCodeBg && !instCodeBg.includes("/") && !instCodeBg.includes("\\") && !instCodeBg.includes(".")) {
      resolvedCode = instCodeBg.trim().toUpperCase();
    } else {
      resolvedCode = "BBHS";
    }
  }

  const aiName = `${resolvedCode} AI`;

  return NextResponse.json({
    success: true,
    code: resolvedCode,
    logo: resolvedLogo,
    name: resolvedName,
    aiName,
  });
}

