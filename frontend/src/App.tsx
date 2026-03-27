import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import DetectionPage from "./pages/DetectionPage";
import EvidencePage from "./pages/EvidencePage";
import IngestPage from "./pages/IngestPage";
import LegalPage from "./pages/LegalPage";

function SplashScreen() {
  return (
    <motion.div
      className="fixed inset-0 z-[100] overflow-hidden bg-abyss"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.55, ease: "easeInOut" } }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_35%,rgba(0,234,255,0.18),transparent_25%),radial-gradient(circle_at_50%_50%,rgba(212,255,0,0.16),transparent_34%)]" />
      <div className="absolute inset-0 scanline-overlay opacity-40" />
      <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full border border-neon/20 bg-neon/5 blur-3xl" />

      <div className="relative flex min-h-screen flex-col items-center justify-center px-6 text-center">
        <motion.div
          className="splash-ring"
          initial={{ scale: 0.82, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />

        <motion.div
          className="font-display text-[0.7rem] uppercase tracking-[0.55em] text-neon"
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.5 }}
        >
          Initializing Sentinel Grid
        </motion.div>

        <motion.h1
          className="splash-title mt-5 font-display text-6xl uppercase tracking-[0.22em] text-white sm:text-7xl md:text-8xl"
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.25, duration: 0.7, ease: "easeOut" }}
        >
          Sentinel
        </motion.h1>

        <motion.div
          className="mt-5 font-body text-base uppercase tracking-[0.38em] text-slate-300 sm:text-lg"
          initial={{ y: 12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.55 }}
        >
          Real-Time Media Fingerprinting Engine
        </motion.div>

        <motion.div
          className="mt-10 h-1.5 w-64 overflow-hidden rounded-full border border-neon/20 bg-slate-950/80 sm:w-80"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.55, duration: 0.35 }}
        >
          <motion.div
            className="h-full bg-[linear-gradient(90deg,#00eaff_0%,#d4ff00_65%,#f5ff9a_100%)] shadow-[0_0_24px_rgba(212,255,0,0.7)]"
            initial={{ x: "-100%" }}
            animate={{ x: "0%" }}
            transition={{ delay: 0.65, duration: 1.1, ease: "easeInOut" }}
          />
        </motion.div>
      </div>
    </motion.div>
  );
}

export default function App() {
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setShowSplash(false);
    }, 2200);

    return () => window.clearTimeout(timeout);
  }, []);

  return (
    <>
      <AnimatePresence>{showSplash ? <SplashScreen /> : null}</AnimatePresence>
      <Routes>
        <Route path="/" element={<Navigate to="/ingest" replace />} />
        <Route element={<AppLayout />}>
          <Route path="/ingest" element={<IngestPage />} />
          <Route path="/detection" element={<DetectionPage />} />
          <Route path="/evidence" element={<EvidencePage />} />
          <Route path="/legal" element={<LegalPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/ingest" replace />} />
      </Routes>
    </>
  );
}
