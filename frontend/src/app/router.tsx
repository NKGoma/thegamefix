import { createBrowserRouter } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Experiments } from "./routes/Experiments";
import { Models } from "./routes/Models";
import { Overview } from "./routes/Overview";
import { Personas } from "./routes/Personas";
import { Runs } from "./routes/Runs";
import { Settings } from "./routes/Settings";

// Single place where the router is created; the static viewer (M7) swaps this for a hash router.
export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Overview /> },
      { path: "/experiments", element: <Experiments /> },
      { path: "/runs", element: <Runs /> },
      { path: "/personas", element: <Personas /> },
      { path: "/models", element: <Models /> },
      { path: "/settings", element: <Settings /> },
    ],
  },
]);
