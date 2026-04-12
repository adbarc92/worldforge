import { describe, it, expect } from "vitest";
import { Routes, Route } from "react-router-dom";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { Shell } from "./Shell";

describe("Shell", () => {
  it("renders the sidebar and nested routes via <Outlet />", () => {
    renderWithProviders(
      <Routes>
        <Route element={<Shell />}>
          <Route path="/" element={<div>Child content</div>} />
        </Route>
      </Routes>,
    );
    expect(screen.getByText("Canon Builder")).toBeInTheDocument();
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });
});
