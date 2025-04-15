"use client";
import { useAuthenticator } from "@aws-amplify/ui-react";
import { useEffect, useState } from "react";
import { Amplify } from "aws-amplify";
import { fetchAuthSession } from "aws-amplify/auth";
import "./../app/app.css";
import outputs from "@/amplify_outputs.json";

Amplify.configure(outputs);

interface ApiResponse {
  error?: string;
  [key: string]: any;
}

const ALLOWED_ENDPOINTS = ["role", "devices", "download"];

export default function App() {
  const { signOut } = useAuthenticator();
  const [apiData, setApiData] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [s3filePath, sets3FilePath] = useState("");
  const [userRole, setUserRole] = useState<string>(""); // Separate state for user role

  const makeAuthenticatedRequest = async (
    endpoint: string,
    method: string,
    queryParams?: Record<string, string>,
    body?: object
  ) => {
    setIsLoading(true);
    try {
      // Validate endpoint
      if (!ALLOWED_ENDPOINTS.includes(endpoint)) {
        throw new Error("Invalid endpoint");
      }

      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) {
        throw new Error("No token available");
      }

      let url = `/api/${endpoint}`;
      if (queryParams) {
        const params = new URLSearchParams(queryParams);
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        ...(body && { body: JSON.stringify(body) }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error, status: ${response.status}`);
      }

      const data = await response.json();

      if (endpoint !== "role") {
        setApiData(data);
      }
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "An unknown error occurred";
      console.error("Error:", errorMessage);
      if (endpoint !== "role") {
        setApiData({ error: errorMessage });
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserRole = async () => {
    try {
      const roleData = await makeAuthenticatedRequest("role", "GET");
      const groupValue = roleData.group || null;
      setUserRole(groupValue);
    } catch (error) {
      console.error("Error fetching user role:", error);
      setUserRole("null");
    }
  };

  const listDevices = () => makeAuthenticatedRequest("devices", "GET");
  const downloadFile = () =>
    makeAuthenticatedRequest("download", "POST", { s3Path: s3filePath });

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        await fetchAuthSession();
        await fetchUserRole();
      } catch (err) {
        console.error("Authentication verification failed:", err);
      }
    };

    verifyAuth();
  }, []);

  // Sanitize s3filePath input
  const handleS3FilePathChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const sanitizedPath = e.target.value.replace(/[^a-zA-Z0-9-_./]/g, "");
    sets3FilePath(sanitizedPath);
  };

  return (
    <main>
      <h1>Welcome to the AVP IoT app</h1>
      <div className="main-content-block">
        <p className="paragraphs">
          You're logged in as:{" "}
          <b>{userRole ? userRole : "user is not assigned to group"}</b>
        </p>
        <p className="paragraphs">Accessible from managers and operators</p>
        <button onClick={listDevices} disabled={isLoading}>
          {isLoading ? "Loading..." : "List Devices"}
        </button>

        <p className="paragraphs">Accessible from managers only</p>
        <input
          type="text"
          value={s3filePath}
          onChange={(e) => sets3FilePath(e.target.value)}
          placeholder="Enter S3 file path"
          className="input-box"
          aria-label="S3 file path input"
        />
        <button onClick={downloadFile} disabled={isLoading}>
          Download File
        </button>

        <button onClick={signOut} className="signout-button">
          Sign out
        </button>

        {apiData && (
          <div>
            <h2 className="paragraphs">Result from API:</h2>
            <pre>{JSON.stringify(apiData, null, 2)}</pre>
          </div>
        )}
      </div>
    </main>
  );
}
