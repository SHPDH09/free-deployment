import { Suspense } from "react";
import AuthCallbackPage from "./page-content";

export default function Page() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">Loading...</div>}>
      <AuthCallbackPage />
    </Suspense>
  );
}
