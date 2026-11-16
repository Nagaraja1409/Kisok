"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";

const AdminDashboard = dynamic(() => import("@/components/AdminDashboard"), {
  ssr: false,
});

export default function AdminPage() {
  const router = useRouter();
  return <AdminDashboard onBackToKiosk={() => router.push("/dashboard")} />;
}
