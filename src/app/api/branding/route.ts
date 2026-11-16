import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * Ensures .env and .env.local are kept in sync with .env.example
 */
function syncEnvFiles() {
  try {
    const cwd = process.cwd();
    const examplePath = path.join(cwd, ".env.example");
    if (fs.existsSync(examplePath)) {
      const exampleContent = fs.readFileSync(examplePath, "utf-8");
      const targetFiles = [".env", ".env.local"];
      for (const target of targetFiles) {
        const targetPath = path.join(cwd, target);
        if (!fs.existsSync(targetPath) || fs.readFileSync(targetPath, "utf-8") !== exampleContent) {
          fs.writeFileSync(targetPath, exampleContent, "utf-8");
        }
      }
    }
  } catch {
    // ignore
  }
}

/**
 * Reads variable from disk files directly so changes in .env.example / .env / .env.local take effect immediately.
 */
function readEnv(key: string): string {
  const files = [".env.example", ".env.local", ".env", ".env.development"];
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

  if (process.env[key] && process.env[key]!.trim() !== "") {
    return process.env[key]!.trim().replace(/^["']|["']$/g, "");
  }

  return "";
}

/**
 * GET /api/branding
 * Dynamically returns code, name, logo, aiName, and background image (backgroupdlo)
 * strictly from the environment configuration with zero caching.
 */
export async function GET() {
  syncEnvFiles();

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

  const rawAiName =
    readEnv("NEXT_PUBLIC_AI_NAME") ||
    readEnv("AI_NAME") ||
    readEnv("NEXT_PUBLIC_AI_ASSISTANT_NAME") ||
    readEnv("AI_ASSISTANT_NAME") ||
    readEnv("NEXT_PUBLIC_COPILOT_NAME") ||
    readEnv("COPILOT_NAME") ||
    "";

  const aiName = rawAiName.trim() || `${resolvedCode} AI`;

  const backgroupdlo = (
    readEnv("backgroupdlo") ||
    readEnv("NEXT_PUBLIC_BACKGROUPDLO") ||
    readEnv("BACKGROUND_IMAGE") ||
    readEnv("NEXT_PUBLIC_BACKGROUND_IMAGE") ||
    ""
  ).trim();

  return NextResponse.json(
    {
      success: true,
      code: resolvedCode,
      logo: resolvedLogo,
      name: resolvedName,
      aiName,
      backgroupdlo,
    },
    {
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
        Pragma: "no-cache",
        Expires: "0",
      },
    }
  );
}
