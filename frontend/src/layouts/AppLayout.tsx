import { AnimatePresence, motion } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

export default function AppLayout() {
  const location = useLocation();

  return (
    <div className="relative min-h-screen overflow-hidden bg-abyss font-body text-ink">
      <div className="pointer-events-none absolute inset-0 scanline-overlay opacity-5" />
      <div className="relative z-10 grid min-h-screen lg:grid-cols-[280px_1fr]">
        <div className="hidden lg:block">
          <Sidebar />
        </div>

        <main className="flex min-h-screen flex-col gap-5 px-4 py-4 md:px-6 md:py-6">
          <Topbar />
          <div className="lg:hidden">
            <Sidebar />
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -18 }}
              transition={{ duration: 0.28, ease: "easeOut" }}
              className="flex-1"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
