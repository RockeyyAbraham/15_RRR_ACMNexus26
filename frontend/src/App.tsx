import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import DetectionPage from "./pages/DetectionPage";
import EvidencePage from "./pages/EvidencePage";
import IngestPage from "./pages/IngestPage";
import LegalPage from "./pages/LegalPage";

export default function App() {
  return (
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
  );
}
