import { ApiError } from "./client";

export interface ArtifactMetadata {
  artifact_id: string;
  sha256: string;
  size_bytes: number;
  manifest: {
    format_version: number;
    name: string;
    entrypoint: string;
    input_file: string;
    requirements_file: string;
    output_file: string;
    timeout_seconds: number;
  };
}

export async function uploadArtifact(file: File): Promise<ArtifactMetadata> {
  if (!file.name.toLowerCase().endsWith(".zip")) {
    throw new Error("Select a ZIP workload package.");
  }

  if (file.size > 50 * 1024 * 1024) {
    throw new Error("The ZIP file exceeds the 50 MiB upload limit.");
  }

  let response: Response;
  try {
    response = await fetch("/api/v1/artifacts", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/zip",
      },
      body: file,
    });
  } catch {
    throw new Error("Cannot connect to the DABALLS controller. Check that it is running.");
  }

  if (!response.ok) {
    let message = `Artifact upload failed (${response.status}).`;
    try {
      const body: unknown = await response.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof body.detail === "string"
      ) {
        message = body.detail;
      }
    } catch {
      // Keep the HTTP error message.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as ArtifactMetadata;
}
