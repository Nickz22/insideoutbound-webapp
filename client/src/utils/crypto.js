// Helper function to generate a code verifier and code challenge
export const generatePKCEChallenge = async () => {
    const array = new Uint8Array(32);
    window.crypto.getRandomValues(array);
    const codeVerifier = Array.from(array, (byte) =>
      byte.toString(16).padStart(2, "0")
    ).join("");
    const encoder = new TextEncoder();
    const codeData = encoder.encode(codeVerifier);
    const digest = await window.crypto.subtle.digest("SHA-256", codeData);
    const base64Digest = btoa(String.fromCharCode(...new Uint8Array(digest)));
    const codeChallenge = base64Digest
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
    return { codeVerifier, codeChallenge };
  };