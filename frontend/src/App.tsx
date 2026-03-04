import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { ProjectProvider } from "@/contexts/ProjectContext";
import { Shell } from "@/components/layout/Shell";
import { DocumentsPage } from "@/pages/DocumentsPage";
import { ChatPage } from "@/pages/ChatPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { ProjectsPage } from "@/pages/ProjectsPage";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Shell />}>
              <Route path="/" element={<ChatPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ProjectProvider>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
