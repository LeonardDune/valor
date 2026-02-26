// @ts-ignore: Deno types - install the Deno VSCode extension to resolve
import "@supabase/functions-js/edge-runtime.d.ts";
import { Resend } from "npm:resend";

const resend = new Resend(Deno.env.get("RESEND_API_KEY"));
const FROM_EMAIL = Deno.env.get("FROM_EMAIL") ?? "noreply@contact.valor-ecosystem.nl";
const HOOK_SECRET = Deno.env.get("HOOK_SECRET");

async function verifySignature(secret: string, body: string, authHeader: string | null): Promise<boolean> {
  if (!authHeader) return false;
  const token = authHeader.replace("Bearer ", "");
  const rawSecret = secret.replace("v1,whsec_", "");
  const keyData = Uint8Array.from(atob(rawSecret), c => c.charCodeAt(0));
  const key = await crypto.subtle.importKey("raw", keyData, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  const expected = Array.from(new Uint8Array(signature)).map(b => b.toString(16).padStart(2, "0")).join("");
  return token === expected;
}

Deno.serve(async (req) => {
  const bodyText = await req.text();

  if (HOOK_SECRET) {
    const valid = await verifySignature(HOOK_SECRET, bodyText, req.headers.get("authorization"));
    if (!valid) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }
  }

  const { user, email_data } = JSON.parse(bodyText);

  try {
    await resend.emails.send({
      from: FROM_EMAIL,
      to: user.email,
      subject: email_data.subject,
      html: email_data.html_body,
    });

    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Failed to send auth email:", error);
    return new Response(JSON.stringify({ error: String(error) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
