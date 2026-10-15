import { z } from "zod";

/**
 * Zod validation schema for chat input messages.
 */
export const chatInputSchema = z
  .string()
  .trim()
  .min(1, "Please type a question or message")
  .max(3000, "Message cannot exceed 3000 characters");

/**
 * Zod validation schema for Job Description evaluations.
 */
export const jdInputSchema = z
  .string()
  .trim()
  .min(20, "Job description should be at least 20 characters for meaningful analysis")
  .max(12000, "Job description cannot exceed 12,000 characters");

/**
 * File upload validation parameters.
 */
export const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB
export const ACCEPTED_FILE_TYPES = ["application/pdf"];

export function validateResumeFile(file: File): { valid: boolean; error?: string } {
  if (!file) {
    return { valid: false, error: "Please select a file to upload" };
  }

  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    return { valid: false, error: "Only PDF format (.pdf) is supported" };
  }

  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: "File size exceeds the 15MB limit" };
  }

  return { valid: true };
}
