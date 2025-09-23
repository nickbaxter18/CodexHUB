import express from "express";
import healthRoutes from "./health.js";
import fileRoutes from "./files.js";
import gitRoutes from "./git.js";
import logRoutes from "./logs.js";
import taskRoutes from "./tasks.js";

const router = express.Router();

router.use("/", healthRoutes);
router.use("/files", fileRoutes);
router.use("/git", gitRoutes);
router.use("/logs", logRoutes);
router.use("/tasks", taskRoutes);

export default router;