"use client";

import React, { useState, useEffect } from "react";
import {
  CampusInfoData,
  CampusBranding,
  LeadershipMember,
  TourFacility,
  GalleryItem,
  CampusEvent,
  CampusAchievement,
} from "@/types/campus";
import KioskLivePreviewModal from "@/components/admin/KioskLivePreviewModal";
import {
  Building2,
  Sparkles,
  Save,
  Eye,
  Plus,
  Trash2,
  Upload,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Video,
  Image as ImageIcon,
  Users,
  MapPin,
  Calendar,
  Award,
  Layers,
  ArrowUp,
  ArrowDown,
  RotateCcw,
} from "lucide-react";

type CmsTab =
  | "branding"
  | "hero"
  | "leadership"
  | "facilities"
  | "gallery"
  | "events"
  | "achievements"
  | "stats";

export default function PortalCmsManager() {
  const [data, setData] = useState<CampusInfoData | null>(null);
  const [savedSnapshot, setSavedSnapshot] = useState<string>("");
  const [activeTab, setActiveTab] = useState<CmsTab>("branding");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveStatus, setSaveStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);
  const [uploadingField, setUploadingField] = useState<string | null>(null);

  // Fetch initial data
  const loadData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/admin/campus-info");
      if (res.ok) {
        const json = await res.json();
        setData(json);
        setSavedSnapshot(JSON.stringify(json));
      } else {
        // Fallback to public endpoint
        const fallbackRes = await fetch("/api/kiosk/campus-info");
        const json = await fallbackRes.json();
        setData(json);
        setSavedSnapshot(JSON.stringify(json));
      }
    } catch (e: any) {
      console.error("Failed to load campus info in CMS:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const hasUnsavedChanges = data ? JSON.stringify(data) !== savedSnapshot : false;

  // Publish / Save handler
  const handlePublish = async () => {
    if (!data) return;
    setIsSaving(true);
    setSaveStatus(null);

    try {
      const res = await fetch("/api/admin/campus-info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const resJson = await res.json();
      if (res.ok && resJson.success) {
        setSavedSnapshot(JSON.stringify(data));
        setSaveStatus({
          type: "success",
          message: "Published successfully! Terminals on /dashboard will immediately reflect these changes.",
        });
        setIsPreviewOpen(false);
      } else {
        setSaveStatus({
          type: "error",
          message: resJson.error || "Failed to publish changes.",
        });
      }
    } catch (err: any) {
      setSaveStatus({
        type: "error",
        message: err.message || "Network error while saving.",
      });
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveStatus(null), 6000);
    }
  };

  // File upload handler
  const handleFileUpload = async (
    file: File,
    category: string,
    onSuccess: (url: string) => void
  ) => {
    const uploadId = `${category}-${Date.now()}`;
    setUploadingField(uploadId);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("category", category);

      const res = await fetch("/api/admin/campus-info/upload", {
        method: "POST",
        body: formData,
      });

      const result = await res.json();
      if (res.ok && result.success && result.url) {
        onSuccess(result.url);
      } else {
        alert(result.error || "Upload failed. Please try again.");
      }
    } catch (error: any) {
      alert(`File upload failed: ${error.message}`);
    } finally {
      setUploadingField(null);
    }
  };

  if (isLoading || !data) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
        <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 1rem", color: "#ea580c" }} />
        <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>Loading Campus CMS Configuration...</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", paddingBottom: "2rem" }}>
      {/* Top CMS Header & Action Bar */}
      <div
        style={{
          background: "#ffffff",
          borderRadius: "16px",
          border: "1px solid #e2e8f0",
          boxShadow: "0 4px 18px rgba(15, 23, 42, 0.04)",
          padding: "1.25rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
            <span
              style={{
                background: "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)",
                color: "#ffffff",
                padding: "6px",
                borderRadius: "10px",
                display: "flex",
              }}
            >
              <Building2 size={20} />
            </span>
            <div>
              <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 800, color: "#0e2a47" }}>
                Campus Portal CMS (Dashboard Manager)
              </h2>
              <p style={{ margin: "2px 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                Dynamically customize all media, leadership statements, facilities, gallery, and schedules displayed on /dashboard
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {hasUnsavedChanges ? (
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "#d97706",
                background: "#fef3c7",
                padding: "4px 10px",
                borderRadius: "9999px",
                border: "1px solid #fde68a",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <AlertCircle size={13} /> Unsaved Changes in Draft
            </span>
          ) : (
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "#059669",
                background: "#dcfce7",
                padding: "4px 10px",
                borderRadius: "9999px",
                border: "1px solid #bbf7d0",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <CheckCircle2 size={13} /> Synchronized with Kiosks
            </span>
          )}

          {/* PREVIEW BUTTON */}
          <button
            onClick={() => setIsPreviewOpen(true)}
            style={{
              background: "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
              color: "#ffffff",
              border: "none",
              borderRadius: "10px",
              padding: "0.6rem 1.15rem",
              fontSize: "0.82rem",
              fontWeight: 800,
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: "pointer",
              boxShadow: "0 4px 12px rgba(2, 132, 199, 0.3)",
            }}
          >
            <Eye size={16} /> Live Preview Kiosk
          </button>

          {/* SAVE & PUBLISH BUTTON */}
          <button
            onClick={handlePublish}
            disabled={isSaving || !hasUnsavedChanges}
            style={{
              background:
                !hasUnsavedChanges
                  ? "#94a3b8"
                  : "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)",
              color: "#ffffff",
              border: "none",
              borderRadius: "10px",
              padding: "0.6rem 1.25rem",
              fontSize: "0.82rem",
              fontWeight: 800,
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: !hasUnsavedChanges || isSaving ? "not-allowed" : "pointer",
              boxShadow: hasUnsavedChanges ? "0 4px 14px rgba(234, 88, 12, 0.35)" : "none",
            }}
          >
            <Save size={16} /> {isSaving ? "Publishing..." : "Save & Publish to Kiosk"}
          </button>
        </div>
      </div>

      {/* Save Notification Banner */}
      {saveStatus && (
        <div
          style={{
            padding: "0.85rem 1.25rem",
            borderRadius: "12px",
            background: saveStatus.type === "success" ? "#ecfdf5" : "#fef2f2",
            border: `1.5px solid ${saveStatus.type === "success" ? "#a7f3d0" : "#fecaca"}`,
            color: saveStatus.type === "success" ? "#065f46" : "#991b1b",
            fontSize: "0.82rem",
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          {saveStatus.type === "success" ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{saveStatus.message}</span>
        </div>
      )}

      {/* Tabs Navigation */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          background: "#f1f5f9",
          padding: "6px",
          borderRadius: "14px",
          overflowX: "auto",
        }}
      >
        {[
          { id: "branding" as CmsTab, label: "Branding & Ticker", icon: Building2 },
          { id: "hero" as CmsTab, label: "Hero Video & Reel", icon: Video },
          { id: "leadership" as CmsTab, label: "Leadership Desk", icon: Users },
          { id: "facilities" as CmsTab, label: "Campus Facilities", icon: MapPin },
          { id: "gallery" as CmsTab, label: "Photo Gallery", icon: ImageIcon },
          { id: "events" as CmsTab, label: "Upcoming Events", icon: Calendar },
          { id: "achievements" as CmsTab, label: "Wall of Fame", icon: Award },
          { id: "stats" as CmsTab, label: "Campus Telemetry", icon: Sparkles },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "0.55rem 1rem",
                borderRadius: "10px",
                border: "none",
                background: isActive ? "#ffffff" : "transparent",
                color: isActive ? "#ea580c" : "#64748b",
                fontWeight: isActive ? 800 : 600,
                fontSize: "0.82rem",
                cursor: "pointer",
                boxShadow: isActive ? "0 2px 8px rgba(0, 0, 0, 0.06)" : "none",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT PANELS */}
      <div
        style={{
          background: "#ffffff",
          borderRadius: "16px",
          border: "1px solid #e2e8f0",
          padding: "1.5rem",
          boxShadow: "0 4px 20px rgba(15, 23, 42, 0.03)",
        }}
      >
        {/* =========================================================================
           TAB 1: BRANDING & TICKER NOTICES
           ========================================================================= */}
        {activeTab === "branding" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
              Institution Identity & Announcements
            </h3>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.2rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Institute Name (Overrides .env default if filled)
                </label>
                <input
                  type="text"
                  value={data.branding.instituteName}
                  placeholder="e.g. Madhuvan Vatika Public School"
                  onChange={(e) =>
                    setData({
                      ...data,
                      branding: { ...data.branding, instituteName: e.target.value },
                    })
                  }
                  style={{
                    width: "100%",
                    padding: "0.6rem 0.85rem",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.85rem",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Institute Short Code
                </label>
                <input
                  type="text"
                  value={data.branding.shortCode}
                  placeholder="e.g. MVPS"
                  onChange={(e) =>
                    setData({
                      ...data,
                      branding: { ...data.branding, shortCode: e.target.value },
                    })
                  }
                  style={{
                    width: "100%",
                    padding: "0.6rem 0.85rem",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.85rem",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Motto / Core Tagline
                </label>
                <input
                  type="text"
                  value={data.branding.motto}
                  placeholder="e.g. Empowering Minds, Shaping Futures"
                  onChange={(e) =>
                    setData({
                      ...data,
                      branding: { ...data.branding, motto: e.target.value },
                    })
                  }
                  style={{
                    width: "100%",
                    padding: "0.6rem 0.85rem",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.85rem",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Affiliation & Accreditations
                </label>
                <input
                  type="text"
                  value={data.branding.affiliation}
                  placeholder="e.g. CBSE Affiliation No. 1930281 | NAAC Grade A++"
                  onChange={(e) =>
                    setData({
                      ...data,
                      branding: { ...data.branding, affiliation: e.target.value },
                    })
                  }
                  style={{
                    width: "100%",
                    padding: "0.6rem 0.85rem",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
            </div>

            {/* Logo Image Upload */}
            <div
              style={{
                background: "#f8fafc",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                padding: "1rem",
                display: "flex",
                alignItems: "center",
                gap: "1.5rem",
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: "12px",
                  background: "#ffffff",
                  border: "1.5px solid #cbd5e1",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  overflow: "hidden",
                }}
              >
                {data.branding.logo ? (
                  <img src={data.branding.logo} alt="Logo" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
                ) : (
                  <Building2 size={24} style={{ color: "#94a3b8" }} />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ margin: "0 0 4px", fontSize: "0.88rem", fontWeight: 700 }}>Custom Logo Asset</h4>
                <p style={{ margin: "0 0 8px", fontSize: "0.75rem", color: "#64748b" }}>
                  Upload a high-resolution PNG or SVG logo. If left blank, automatically loads the .env logo.
                </p>
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                  <input
                    type="file"
                    accept="image/*"
                    id="logo-upload"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        handleFileUpload(file, "brand", (url) => {
                          setData({ ...data, branding: { ...data.branding, logo: url } });
                        });
                      }
                    }}
                  />
                  <label
                    htmlFor="logo-upload"
                    style={{
                      background: "#ea580c",
                      color: "#ffffff",
                      borderRadius: "6px",
                      padding: "0.35rem 0.85rem",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <Upload size={13} /> {uploadingField?.startsWith("brand") ? "Uploading..." : "Upload Logo"}
                  </label>
                  {data.branding.logo && (
                    <button
                      onClick={() => setData({ ...data, branding: { ...data.branding, logo: "" } })}
                      style={{
                        background: "transparent",
                        border: "1px solid #cbd5e1",
                        color: "#ef4444",
                        borderRadius: "6px",
                        padding: "0.35rem 0.75rem",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Reset to .env Default
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Live Ticker Bullet Points */}
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                <h4 style={{ margin: 0, fontSize: "0.92rem", fontWeight: 700 }}>
                  Marquee Announcement Ticker (Top Headline Banner)
                </h4>
                <button
                  onClick={() =>
                    setData({
                      ...data,
                      branding: {
                        ...data.branding,
                        tickerNotices: [...data.branding.tickerNotices, "New campus announcement notice."],
                      },
                    })
                  }
                  style={{
                    background: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    padding: "0.35rem 0.75rem",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <Plus size={13} /> Add Notice
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {data.branding.tickerNotices.map((notice, idx) => (
                  <div key={idx} style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input
                      type="text"
                      value={notice}
                      onChange={(e) => {
                        const updated = [...data.branding.tickerNotices];
                        updated[idx] = e.target.value;
                        setData({ ...data, branding: { ...data.branding, tickerNotices: updated } });
                      }}
                      style={{
                        flex: 1,
                        padding: "0.5rem 0.8rem",
                        borderRadius: "8px",
                        border: "1px solid #cbd5e1",
                        fontSize: "0.82rem",
                      }}
                    />
                    <button
                      onClick={() => {
                        const updated = data.branding.tickerNotices.filter((_, i) => i !== idx);
                        setData({ ...data, branding: { ...data.branding, tickerNotices: updated } });
                      }}
                      style={{
                        background: "#fee2e2",
                        border: "1px solid #fecaca",
                        color: "#ef4444",
                        borderRadius: "8px",
                        width: "34px",
                        height: "34px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 2: HERO VIDEO & STAGE REEL
           ========================================================================= */}
        {activeTab === "hero" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
              Hero Promo Video & Stage Configuration
            </h3>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.2rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Hero Headline
                </label>
                <input
                  type="text"
                  value={data.hero.headline}
                  onChange={(e) => setData({ ...data, hero: { ...data.hero, headline: e.target.value } })}
                  style={{
                    width: "100%",
                    padding: "0.6rem 0.85rem",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.85rem",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Sub-headline Description
                </label>
                <input
                  type="text"
                  value={data.hero.subheadline}
                  onChange={(e) => setData({ ...data, hero: { ...data.hero, subheadline: e.target.value } })}
                  style={{
                    width: "100%",
                    padding: "0.6rem 0.85rem",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
            </div>

            {/* Video File / URL Manager */}
            <div
              style={{
                background: "#f8fafc",
                borderRadius: "14px",
                border: "1px solid #e2e8f0",
                padding: "1.25rem",
                display: "grid",
                gridTemplateColumns: "minmax(260px, 320px) 1fr",
                gap: "1.5rem",
                alignItems: "center",
              }}
            >
              <div
                style={{
                  height: "170px",
                  borderRadius: "10px",
                  background: "#0f172a",
                  overflow: "hidden",
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {data.hero.videoUrl ? (
                  <video
                    src={data.hero.videoUrl}
                    poster={data.hero.posterUrl}
                    controls
                    muted
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                ) : (
                  <Video size={36} style={{ color: "#475569" }} />
                )}
              </div>

              <div>
                <h4 style={{ margin: "0 0 6px", fontSize: "0.95rem", fontWeight: 800 }}>
                  Active Campus Promo Video (MP4)
                </h4>
                <p style={{ margin: "0 0 10px", fontSize: "0.76rem", color: "#64748b" }}>
                  Upload a 15–30 second high-definition campus promo reel or specify an existing public asset path.
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <input
                    type="text"
                    value={data.hero.videoUrl}
                    onChange={(e) => setData({ ...data, hero: { ...data.hero, videoUrl: e.target.value } })}
                    placeholder="/campus_promo.mp4"
                    style={{
                      width: "100%",
                      padding: "0.55rem 0.85rem",
                      borderRadius: "8px",
                      border: "1px solid #cbd5e1",
                      fontSize: "0.82rem",
                    }}
                  />

                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <input
                      type="file"
                      accept="video/mp4,video/webm"
                      id="hero-video-upload"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleFileUpload(file, "hero", (url) => {
                            setData({ ...data, hero: { ...data.hero, videoUrl: url } });
                          });
                        }
                      }}
                    />
                    <label
                      htmlFor="hero-video-upload"
                      style={{
                        background: "#ea580c",
                        color: "#ffffff",
                        borderRadius: "6px",
                        padding: "0.4rem 0.85rem",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      <Upload size={13} /> {uploadingField?.startsWith("hero") ? "Uploading Video..." : "Upload New MP4"}
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 3: LEADERSHIP VISION DESK
           ========================================================================= */}
        {activeTab === "leadership" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
                  Leadership Desk &amp; Visionaries
                </h3>
                <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "#64748b" }}>
                  Configure Chairman, Principal, Director, and Executive leadership cards &amp; full vision dialogues.
                </p>
              </div>

              <button
                onClick={() => {
                  const newLeader: LeadershipMember = {
                    id: `leader_${Date.now()}`,
                    name: "New Executive Leader",
                    designation: "Dean / Trustee",
                    image: "/mvps/leadership/principal_deepak_puri.jpg",
                    quotePreview: "Inspiring future generations through excellence in holistic learning.",
                    fullQuote: "Welcome to our esteemed institution. We nurture values, intellect, and character.",
                    order: data.leadership.length + 1,
                    active: true,
                  };
                  setData({ ...data, leadership: [...data.leadership, newLeader] });
                }}
                style={{
                  background: "#ea580c",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "0.45rem 0.95rem",
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  cursor: "pointer",
                }}
              >
                <Plus size={14} /> Add Leader
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
              {data.leadership.map((leader, idx) => (
                <div
                  key={leader.id}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: "14px",
                    padding: "1.25rem",
                    display: "grid",
                    gridTemplateColumns: "100px 1fr auto",
                    gap: "1.2rem",
                    alignItems: "start",
                  }}
                >
                  {/* Photo & Upload */}
                  <div style={{ textAlign: "center" }}>
                    <div
                      style={{
                        width: 90,
                        height: 90,
                        borderRadius: "12px",
                        overflow: "hidden",
                        border: "2px solid #ea580c",
                        margin: "0 auto 6px",
                        background: "#ffffff",
                      }}
                    >
                      <img src={leader.image} alt={leader.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </div>

                    <input
                      type="file"
                      accept="image/*"
                      id={`leader-photo-${idx}`}
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleFileUpload(file, "leadership", (url) => {
                            const updated = [...data.leadership];
                            updated[idx].image = url;
                            setData({ ...data, leadership: updated });
                          });
                        }
                      }}
                    />
                    <label
                      htmlFor={`leader-photo-${idx}`}
                      style={{
                        fontSize: "0.68rem",
                        color: "#ea580c",
                        fontWeight: 700,
                        cursor: "pointer",
                        textDecoration: "underline",
                      }}
                    >
                      Change Photo
                    </label>
                  </div>

                  {/* Form Inputs */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                      <div>
                        <label style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64748b" }}>Full Name</label>
                        <input
                          type="text"
                          value={leader.name}
                          onChange={(e) => {
                            const updated = [...data.leadership];
                            updated[idx].name = e.target.value;
                            setData({ ...data, leadership: updated });
                          }}
                          style={{
                            width: "100%",
                            padding: "0.45rem 0.75rem",
                            borderRadius: "6px",
                            border: "1px solid #cbd5e1",
                            fontSize: "0.82rem",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64748b" }}>Designation</label>
                        <input
                          type="text"
                          value={leader.designation}
                          onChange={(e) => {
                            const updated = [...data.leadership];
                            updated[idx].designation = e.target.value;
                            setData({ ...data, leadership: updated });
                          }}
                          style={{
                            width: "100%",
                            padding: "0.45rem 0.75rem",
                            borderRadius: "6px",
                            border: "1px solid #cbd5e1",
                            fontSize: "0.82rem",
                          }}
                        />
                      </div>
                    </div>

                    <div>
                      <label style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64748b" }}>
                        Quote Preview (Card Short Line)
                      </label>
                      <input
                        type="text"
                        value={leader.quotePreview}
                        onChange={(e) => {
                          const updated = [...data.leadership];
                          updated[idx].quotePreview = e.target.value;
                          setData({ ...data, leadership: updated });
                        }}
                        style={{
                          width: "100%",
                          padding: "0.45rem 0.75rem",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          fontSize: "0.82rem",
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64748b" }}>
                        Full Official Vision Message (Popup Modal Dialogue)
                      </label>
                      <textarea
                        rows={3}
                        value={leader.fullQuote}
                        onChange={(e) => {
                          const updated = [...data.leadership];
                          updated[idx].fullQuote = e.target.value;
                          setData({ ...data, leadership: updated });
                        }}
                        style={{
                          width: "100%",
                          padding: "0.45rem 0.75rem",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          fontSize: "0.82rem",
                          resize: "vertical",
                        }}
                      />
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <button
                      onClick={() => {
                        const updated = data.leadership.filter((_, i) => i !== idx);
                        setData({ ...data, leadership: updated });
                      }}
                      title="Delete Leader"
                      style={{
                        background: "#fee2e2",
                        border: "1px solid #fecaca",
                        color: "#ef4444",
                        borderRadius: "8px",
                        width: "32px",
                        height: "32px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 4: CAMPUS FACILITIES (360 TOUR)
           ========================================================================= */}
        {activeTab === "facilities" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
                  Campus Facilities &amp; Virtual Tour Explorer
                </h3>
                <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "#64748b" }}>
                  Manage the labs, classrooms, sports grounds, and libraries showcased in the 360 virtual tour modal.
                </p>
              </div>

              <button
                onClick={() => {
                  const newFac: TourFacility = {
                    id: `fac_${Date.now()}`,
                    title: "New Scholastic Facility",
                    category: "Innovation Hub",
                    image: "/mvps/facilities/labs.jpg",
                    description: "Modern facility equipped with state-of-the-art interactive pedagogical tools.",
                    highlights: ["Air Conditioned", "Wi-Fi Enabled"],
                    order: data.facilities.length + 1,
                    active: true,
                  };
                  setData({ ...data, facilities: [...data.facilities, newFac] });
                }}
                style={{
                  background: "#ea580c",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "0.45rem 0.95rem",
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  cursor: "pointer",
                }}
              >
                <Plus size={14} /> Add Facility
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
              {data.facilities.map((fac, idx) => (
                <div
                  key={fac.id}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: "14px",
                    overflow: "hidden",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <div style={{ height: "140px", position: "relative", background: "#0f172a" }}>
                    <img src={fac.image} alt={fac.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    <input
                      type="file"
                      accept="image/*"
                      id={`fac-img-${idx}`}
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleFileUpload(file, "facilities", (url) => {
                            const updated = [...data.facilities];
                            updated[idx].image = url;
                            setData({ ...data, facilities: updated });
                          });
                        }
                      }}
                    />
                    <label
                      htmlFor={`fac-img-${idx}`}
                      style={{
                        position: "absolute",
                        bottom: "8px",
                        right: "8px",
                        background: "rgba(0, 0, 0, 0.75)",
                        color: "#fff",
                        padding: "3px 8px",
                        borderRadius: "6px",
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        cursor: "pointer",
                        backdropFilter: "blur(4px)",
                      }}
                    >
                      Change Photo
                    </label>
                  </div>

                  <div style={{ padding: "1rem", display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                    <input
                      type="text"
                      value={fac.title}
                      placeholder="Facility Title"
                      onChange={(e) => {
                        const updated = [...data.facilities];
                        updated[idx].title = e.target.value;
                        setData({ ...data, facilities: updated });
                      }}
                      style={{
                        padding: "0.4rem 0.7rem",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        fontSize: "0.85rem",
                        fontWeight: 700,
                      }}
                    />

                    <input
                      type="text"
                      value={fac.category}
                      placeholder="Category e.g. Innovation Hub"
                      onChange={(e) => {
                        const updated = [...data.facilities];
                        updated[idx].category = e.target.value;
                        setData({ ...data, facilities: updated });
                      }}
                      style={{
                        padding: "0.4rem 0.7rem",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        fontSize: "0.78rem",
                      }}
                    />

                    <textarea
                      rows={2}
                      value={fac.description}
                      placeholder="Narrative description..."
                      onChange={(e) => {
                        const updated = [...data.facilities];
                        updated[idx].description = e.target.value;
                        setData({ ...data, facilities: updated });
                      }}
                      style={{
                        padding: "0.4rem 0.7rem",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        fontSize: "0.78rem",
                        resize: "none",
                      }}
                    />

                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "auto" }}>
                      <button
                        onClick={() => {
                          const updated = data.facilities.filter((_, i) => i !== idx);
                          setData({ ...data, facilities: updated });
                        }}
                        style={{
                          background: "#fee2e2",
                          border: "none",
                          color: "#ef4444",
                          borderRadius: "6px",
                          padding: "0.3rem 0.6rem",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 5: PHOTO GALLERY
           ========================================================================= */}
        {activeTab === "gallery" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
                  Campus Life Media Gallery
                </h3>
                <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "#64748b" }}>
                  Upload and organize photos across Academics, Sports, Cultural Arts, and Campus Life.
                </p>
              </div>

              <div style={{ display: "flex", gap: "8px" }}>
                <input
                  type="file"
                  accept="image/*"
                  id="new-gallery-upload"
                  style={{ display: "none" }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      handleFileUpload(file, "gallery", (url) => {
                        const newItem: GalleryItem = {
                          id: `gallery_${Date.now()}`,
                          title: file.name.replace(/\.[^/.]+$/, ""),
                          shortTitle: "Campus Photo",
                          category: "Cultural & Arts",
                          categoryFilter: "cultural",
                          date: "Recent",
                          description: "Captivating campus memory captured on grounds.",
                          src: url,
                        };
                        setData({ ...data, gallery: [newItem, ...data.gallery] });
                      });
                    }
                  }}
                />
                <label
                  htmlFor="new-gallery-upload"
                  style={{
                    background: "#ea580c",
                    color: "#ffffff",
                    borderRadius: "8px",
                    padding: "0.45rem 0.95rem",
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                    cursor: "pointer",
                  }}
                >
                  <Plus size={14} /> Upload New Photo
                </label>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "1rem" }}>
              {data.gallery.map((item, idx) => (
                <div
                  key={item.id}
                  style={{
                    background: "#f8fafc",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                    overflow: "hidden",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <div style={{ height: "130px", background: "#0f172a" }}>
                    <img src={item.src} alt={item.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  </div>
                  <div style={{ padding: "0.75rem", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <input
                      type="text"
                      value={item.title}
                      placeholder="Title"
                      onChange={(e) => {
                        const updated = [...data.gallery];
                        updated[idx].title = e.target.value;
                        setData({ ...data, gallery: updated });
                      }}
                      style={{
                        padding: "0.35rem 0.6rem",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        fontSize: "0.78rem",
                        fontWeight: 700,
                      }}
                    />

                    <select
                      value={item.categoryFilter}
                      onChange={(e) => {
                        const updated = [...data.gallery];
                        updated[idx].categoryFilter = e.target.value as any;
                        setData({ ...data, gallery: updated });
                      }}
                      style={{
                        padding: "0.35rem 0.6rem",
                        borderRadius: "6px",
                        border: "1px solid #cbd5e1",
                        fontSize: "0.75rem",
                      }}
                    >
                      <option value="cultural">Cultural &amp; Arts</option>
                      <option value="sports">Athletics &amp; Sports</option>
                      <option value="academics">Academic Excellence</option>
                      <option value="facilities">Campus Facilities</option>
                    </select>

                    <div style={{ display: "flex", justifyContent: "flex-end" }}>
                      <button
                        onClick={() => {
                          const updated = data.gallery.filter((_, i) => i !== idx);
                          setData({ ...data, gallery: updated });
                        }}
                        style={{
                          background: "#fee2e2",
                          border: "none",
                          color: "#ef4444",
                          borderRadius: "4px",
                          padding: "2px 8px",
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 6: UPCOMING EVENTS & SCHEDULE
           ========================================================================= */}
        {activeTab === "events" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
                  Upcoming Events &amp; Academic Timeline
                </h3>
                <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "#64748b" }}>
                  Events rendered on the front dashboard timeline ribbon.
                </p>
              </div>

              <button
                onClick={() => {
                  const newEv: CampusEvent = {
                    id: `event_${Date.now()}`,
                    day: "25",
                    month: "NOV",
                    name: "Institutional Annual Day",
                    tag: "Fest",
                    tagClass: "fest",
                    venue: "05:00 PM | Grand Auditorium",
                    image: "/Indian Classical Arts on Stage-5.png",
                    cardClass: "cultural-card",
                  };
                  setData({ ...data, events: [...data.events, newEv] });
                }}
                style={{
                  background: "#ea580c",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "0.45rem 0.95rem",
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  cursor: "pointer",
                }}
              >
                <Plus size={14} /> Add Event
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
              {data.events.map((ev, idx) => (
                <div
                  key={ev.id}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                    padding: "1rem",
                    display: "grid",
                    gridTemplateColumns: "80px 1fr 140px auto",
                    gap: "1rem",
                    alignItems: "center",
                  }}
                >
                  <div style={{ textAlign: "center", background: "#ea580c", color: "#fff", padding: "8px", borderRadius: "8px" }}>
                    <input
                      type="text"
                      value={ev.day}
                      onChange={(e) => {
                        const updated = [...data.events];
                        updated[idx].day = e.target.value;
                        setData({ ...data, events: updated });
                      }}
                      style={{ width: "100%", textAlign: "center", fontWeight: 900, background: "transparent", border: "none", color: "#fff", fontSize: "1.2rem" }}
                    />
                    <input
                      type="text"
                      value={ev.month}
                      onChange={(e) => {
                        const updated = [...data.events];
                        updated[idx].month = e.target.value;
                        setData({ ...data, events: updated });
                      }}
                      style={{ width: "100%", textAlign: "center", fontWeight: 700, background: "transparent", border: "none", color: "#fed7aa", fontSize: "0.75rem" }}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <input
                      type="text"
                      value={ev.name}
                      placeholder="Event Name"
                      onChange={(e) => {
                        const updated = [...data.events];
                        updated[idx].name = e.target.value;
                        setData({ ...data, events: updated });
                      }}
                      style={{ padding: "0.4rem 0.7rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.85rem", fontWeight: 700 }}
                    />
                    <input
                      type="text"
                      value={ev.venue}
                      placeholder="Venue & Timing"
                      onChange={(e) => {
                        const updated = [...data.events];
                        updated[idx].venue = e.target.value;
                        setData({ ...data, events: updated });
                      }}
                      style={{ padding: "0.35rem 0.7rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.78rem" }}
                    />
                  </div>

                  <select
                    value={ev.tagClass}
                    onChange={(e) => {
                      const updated = [...data.events];
                      updated[idx].tagClass = e.target.value as any;
                      updated[idx].tag = e.target.options[e.target.selectedIndex].text;
                      setData({ ...data, events: updated });
                    }}
                    style={{ padding: "0.4rem 0.6rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.78rem" }}
                  >
                    <option value="academics">Academics</option>
                    <option value="sports">Sports</option>
                    <option value="stem">STEM</option>
                    <option value="fest">Cultural</option>
                    <option value="ptm">PTM</option>
                  </select>

                  <button
                    onClick={() => {
                      const updated = data.events.filter((_, i) => i !== idx);
                      setData({ ...data, events: updated });
                    }}
                    style={{
                      background: "#fee2e2",
                      border: "none",
                      color: "#ef4444",
                      borderRadius: "6px",
                      width: "32px",
                      height: "32px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 7: ACHIEVEMENTS (WALL OF FAME)
           ========================================================================= */}
        {activeTab === "achievements" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
                  Wall of Fame &amp; Accolades
                </h3>
                <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "#64748b" }}>
                  Record trophies, medals, inter-school victories, and student distinctions.
                </p>
              </div>

              <button
                onClick={() => {
                  const newAch: CampusAchievement = {
                    id: `ach_${Date.now()}`,
                    title: "State Level Competition",
                    badge: "★ 1st Rank",
                    rank: "1st Rank",
                    category: "State Level",
                    date: "Oct 2025",
                    image: "/achievement_science.jpg",
                  };
                  setData({ ...data, achievements: [...data.achievements, newAch] });
                }}
                style={{
                  background: "#ea580c",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "0.45rem 0.95rem",
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  cursor: "pointer",
                }}
              >
                <Plus size={14} /> Add Achievement
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" }}>
              {data.achievements.map((ach, idx) => (
                <div
                  key={ach.id}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #fed7aa",
                    borderRadius: "12px",
                    padding: "1rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <input
                    type="text"
                    value={ach.title}
                    placeholder="Competition Title"
                    onChange={(e) => {
                      const updated = [...data.achievements];
                      updated[idx].title = e.target.value;
                      setData({ ...data, achievements: updated });
                    }}
                    style={{ padding: "0.4rem 0.7rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.85rem", fontWeight: 800 }}
                  />

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                    <input
                      type="text"
                      value={ach.badge}
                      placeholder="Badge e.g. ★ 1st Rank"
                      onChange={(e) => {
                        const updated = [...data.achievements];
                        updated[idx].badge = e.target.value;
                        setData({ ...data, achievements: updated });
                      }}
                      style={{ padding: "0.35rem 0.6rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.78rem" }}
                    />
                    <input
                      type="text"
                      value={ach.date}
                      placeholder="Date e.g. Aug 2025"
                      onChange={(e) => {
                        const updated = [...data.achievements];
                        updated[idx].date = e.target.value;
                        setData({ ...data, achievements: updated });
                      }}
                      style={{ padding: "0.35rem 0.6rem", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.78rem" }}
                    />
                  </div>

                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <button
                      onClick={() => {
                        const updated = data.achievements.filter((_, i) => i !== idx);
                        setData({ ...data, achievements: updated });
                      }}
                      style={{
                        background: "#fee2e2",
                        border: "none",
                        color: "#ef4444",
                        borderRadius: "4px",
                        padding: "3px 8px",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        cursor: "pointer",
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
           TAB 8: CAMPUS TELEMETRY & STATS
           ========================================================================= */}
        {activeTab === "stats" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#0e2a47" }}>
              Campus Telemetry &amp; Quick Statistics
            </h3>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.2rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Total Enrolled Scholars
                </label>
                <input
                  type="text"
                  value={data.quickStats.studentsCount}
                  onChange={(e) =>
                    setData({
                      ...data,
                      quickStats: { ...data.quickStats, studentsCount: e.target.value },
                    })
                  }
                  style={{ width: "100%", padding: "0.55rem 0.8rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Dedicated Faculty Roster
                </label>
                <input
                  type="text"
                  value={data.quickStats.facultyCount}
                  onChange={(e) =>
                    setData({
                      ...data,
                      quickStats: { ...data.quickStats, facultyCount: e.target.value },
                    })
                  }
                  style={{ width: "100%", padding: "0.55rem 0.8rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  GPS Bus Fleet Count
                </label>
                <input
                  type="text"
                  value={data.quickStats.busCount}
                  onChange={(e) =>
                    setData({
                      ...data,
                      quickStats: { ...data.quickStats, busCount: e.target.value },
                    })
                  }
                  style={{ width: "100%", padding: "0.55rem 0.8rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                  Campus Area (Acreage)
                </label>
                <input
                  type="text"
                  value={data.quickStats.campusArea}
                  onChange={(e) =>
                    setData({
                      ...data,
                      quickStats: { ...data.quickStats, campusArea: e.target.value },
                    })
                  }
                  style={{ width: "100%", padding: "0.55rem 0.8rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#334155", marginBottom: 6 }}>
                Footer Creed Motto
              </label>
              <input
                type="text"
                value={data.footerMotto || ""}
                onChange={(e) => setData({ ...data, footerMotto: e.target.value })}
                placeholder="— Together for a Brighter Tomorrow 🍃 —"
                style={{ width: "100%", padding: "0.55rem 0.8rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
              />
            </div>
          </div>
        )}
      </div>

      {/* LIVE PREVIEW MODAL */}
      {data && (
        <KioskLivePreviewModal
          isOpen={isPreviewOpen}
          onClose={() => setIsPreviewOpen(false)}
          draftData={data}
          onPublish={handlePublish}
          isPublishing={isSaving}
        />
      )}
    </div>
  );
}
