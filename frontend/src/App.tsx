import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { Shell } from "@/components/layout/Shell";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Shell />}>
            <Route path="/" element={<div className="p-6">Chat page coming soon</div>} />
            <Route path="/documents" element={<div className="p-6">Documents page coming soon</div>} />
            <Route path="/settings" element={<div className="p-6">Settings page coming soon</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
