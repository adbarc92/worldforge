import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders, userEvent } from "@/test/test-utils";
import { ProjectsPage } from "./ProjectsPage";

describe("ProjectsPage interactions", () => {
  it("opens the create project dialog and creates a project", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProjectsPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    // Click "New Project" to open dialog
    await user.click(screen.getByRole("button", { name: /new project/i }));

    await waitFor(() => {
      expect(screen.getByText(/create new project/i)).toBeInTheDocument();
    });

    // Fill in the name and description
    await user.type(screen.getByPlaceholderText(/my world/i), "New World");
    await user.type(
      screen.getByPlaceholderText(/a brief description/i),
      "A new world setting",
    );

    // Click create button
    await user.click(screen.getByRole("button", { name: /create project/i }));

    // Wait for dialog to close (project created)
    await waitFor(() => {
      expect(screen.queryByText(/create new project/i)).not.toBeInTheDocument();
    });
  });

  it("shows the delete confirmation flow", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProjectsPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    // Click Delete to show confirmation
    await user.click(screen.getByRole("button", { name: /^delete$/i }));

    // Should show Confirm and Cancel buttons
    expect(screen.getByRole("button", { name: /^confirm$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^cancel$/i })).toBeInTheDocument();

    // Click Cancel to dismiss confirmation
    await user.click(screen.getByRole("button", { name: /^cancel$/i }));

    // Should show Delete button again
    expect(screen.getByRole("button", { name: /^delete$/i })).toBeInTheDocument();
  });

  it("deletes a project when confirmation is accepted", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProjectsPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    // Click Delete then Confirm
    await user.click(screen.getByRole("button", { name: /^delete$/i }));
    await user.click(screen.getByRole("button", { name: /^confirm$/i }));

    // Wait for delete to complete
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /^confirm$/i })).not.toBeInTheDocument();
    });
  });

  it("selects a project by clicking Select button", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProjectsPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    // The Select button should be present (project is not yet active)
    const selectBtn = screen.getByRole("button", { name: /^select$/i });
    await user.click(selectBtn);

    // After selecting, should show "Selected"
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /^selected$/i })).toBeDisabled();
    });
  });

  it("does not create project when name is empty", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProjectsPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /new project/i }));

    await waitFor(() => {
      expect(screen.getByText(/create new project/i)).toBeInTheDocument();
    });

    // Create button should be disabled with empty name
    expect(screen.getByRole("button", { name: /create project/i })).toBeDisabled();
  });
});
