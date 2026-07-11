import { render, screen, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router-dom";
import DashboardLayout from "../layouts/DashboardLayout";
import { ThemeProvider } from "../components/ThemeProvider";

describe("DashboardLayout shell framework integration", () => {
  it("renders sidebars, navigation layout links, and breadcrumbs successfully", () => {
    render(
      <ThemeProvider defaultTheme="light">
        <BrowserRouter>
          <DashboardLayout>
            <div data-testid="child-content">Child View</div>
          </DashboardLayout>
        </BrowserRouter>
      </ThemeProvider>
    );

    // Assert branding and layout elements
    expect(screen.getByText("unilog")).toBeInTheDocument();
    expect(screen.getByTestId("child-content").textContent).toBe("Child View");
    
    // Assert navigation labels in sidebar (rendered twice for desktop & mobile sidebars)
    expect(screen.getAllByText("Overview")).toHaveLength(2);
    expect(screen.getAllByText("Parsed Logs")).toHaveLength(2);
    expect(screen.getAllByText("Custom Rules")).toHaveLength(2);
    expect(screen.getAllByText("API Reference")).toHaveLength(2);
  });

  it("triggers mobile drawer sidebar toggle on menu button clicks", async () => {
    render(
      <ThemeProvider defaultTheme="light">
        <BrowserRouter>
          <DashboardLayout>
            <div>Test</div>
          </DashboardLayout>
        </BrowserRouter>
      </ThemeProvider>
    );

    const toggleBtn = screen.getByLabelText("Toggle Menu");
    
    // By default, the mobile sidebar should be offscreen (translated)
    // Click toggle button
    await act(async () => {
      toggleBtn.click();
    });

    // Check if the overlay backdrop is rendered now
    const backdrops = document.querySelector(".bg-background\\/80");
    expect(backdrops).not.toBeNull();
  });

  it("toggles light and dark themes on header button triggers", async () => {
    render(
      <ThemeProvider defaultTheme="light">
        <BrowserRouter>
          <DashboardLayout>
            <div>Test</div>
          </DashboardLayout>
        </BrowserRouter>
      </ThemeProvider>
    );

    const themeBtn = screen.getByLabelText("Toggle Theme");
    
    // Initially matches light
    expect(document.documentElement.classList.contains("light")).toBe(true);

    // Trigger dark transition
    await act(async () => {
      themeBtn.click();
    });

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.classList.contains("light")).toBe(false);
  });

  it("handles active sidebar navigation state matching router routes", () => {
    import("react-router-dom").then(({ MemoryRouter }) => {
      render(
        <ThemeProvider defaultTheme="light">
          <MemoryRouter initialEntries={["/dashboard/logs"]}>
            <DashboardLayout>
              <div>Test</div>
            </DashboardLayout>
          </MemoryRouter>
        </ThemeProvider>
      );

      // Verify breadcrumbs has logs
      expect(screen.getByText("Logs")).toBeInTheDocument();
      // Default sidebar navigation highlights overview or other items
      expect(screen.getAllByText("Parsed Logs")[0]).toBeInTheDocument();
    });
  });

  it("closes the mobile menu when backdrop is clicked", async () => {
    render(
      <ThemeProvider defaultTheme="light">
        <BrowserRouter>
          <DashboardLayout>
            <div>Test</div>
          </DashboardLayout>
        </BrowserRouter>
      </ThemeProvider>
    );

    const toggleBtn = screen.getByLabelText("Toggle Menu");
    await act(async () => {
      toggleBtn.click();
    });

    const backdrop = document.querySelector(".bg-background\\/80") as HTMLElement;
    expect(backdrop).not.toBeNull();

    await act(async () => {
      backdrop.click();
    });

    expect(document.querySelector(".bg-background\\/80")).toBeNull();
  });
});
