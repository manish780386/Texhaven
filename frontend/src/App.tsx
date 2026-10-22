import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Checker from "./pages/Checker";
import Landing from "./pages/Landing";
import Legal from "./pages/Legal";
import MockPay from "./pages/MockPay";
import NotFound from "./pages/NotFound";
import Recipient from "./pages/Recipient";
import Send from "./pages/Send";
import Track from "./pages/Track";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/send" element={<Send />} />
        <Route path="/track/:id" element={<Track />} />
        <Route path="/checker" element={<Checker />} />
        <Route path="/stop/:token" element={<Recipient />} />
        <Route path="/mock-pay/:id" element={<MockPay />} />
        <Route path="/legal" element={<Legal />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
