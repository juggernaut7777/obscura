// background.js v6.0 — Elite Token Bridge
// Architecture reverse-engineered from G-Labs Auth Helper v3.0.0
// Key innovations: on-demand tokens, dynamic site-key, auto-tab, keep-alive

const BRIDGE_URL = "http://127.0.0.1:9877";
const POLL_INTERVAL = 1500;   // Check bridge every 1.5s
const HEARTBEAT_MIN  = 1;     // Passive push every 60s

let isPolling  = false;
let tokenCount = 0;
let lastPush   = 0;

// ─── 1. KEEP-ALIVE ──────────────────────────────────────────────
// Chrome kills idle service workers after 30s.
// Alarms + heartbeat keep it permanently alive (G-Labs technique).

chrome.alarms.create("keepAlive",  { periodInMinutes: 0.4 });   // 24s
chrome.alarms.create("heartbeat",  { periodInMinutes: HEARTBEAT_MIN });

chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === "keepAlive" && !isPolling) startPolling();
    if (alarm.name === "heartbeat") await generateAndPushToken(false, "IMAGE_GENERATION");
});

chrome.runtime.onInstalled.addListener(() => startPolling());
chrome.runtime.onStartup.addListener(() => startPolling());

// Auto-detect when user navigates to Flow
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url && tab.url.includes("labs.google")) {
        if (!isPolling) startPolling();
    }
});

console.log("🟢 [OBSCURA v6] Elite Token Bridge started.");

// ─── 2. BRIDGE POLLING (ON-DEMAND TOKENS) ───────────────────────
// Instead of blindly pushing tokens every 3s (which got us flagged),
// we now ASK the bridge "do you need a fresh token right now?"
// Only when it says yes do we generate one — maximum freshness.

async function startPolling() {
    if (isPolling) return;
    isPolling = true;
    console.log("🔄 [OBSCURA v6] Polling bridge for on-demand token requests...");

    while (isPolling) {
        try {
            const resp = await fetch(`${BRIDGE_URL}/need-token`, {
                signal: AbortSignal.timeout(3000)
            });

             if (resp.ok) {
                 const data = await resp.json();
                 if (data.pendingGeneration) {
                     console.log("🎬 [OBSCURA v6] Bridge requested in-browser video generation:", data.pendingGeneration);
                     await generateVideoInBrowser(data.pendingGeneration);
                 } else if (data.need) {
                     if (data.action === "RELOAD") {
                         console.log("🔄 [OBSCURA v6] Bridge requested reload. Reloading extension...");
                         chrome.runtime.reload();
                         return;
                     }
                     console.log(`⚡ [OBSCURA v6] Bridge needs FRESH token for ${data.action}! Generating NOW...`);
                     await generateAndPushToken(true, data.action || "IMAGE_GENERATION");
                 }
             }
        } catch (e) {
            // Bridge not running — that's fine, we'll keep trying
        }

        await sleep(POLL_INTERVAL);
    }
}

// ─── 3. TOKEN GENERATION (THE CORE) ─────────────────────────────
// Uses chrome.scripting.executeScript in MAIN world (G-Labs technique).
// This lets us access Google's internal grecaptcha object directly
// from the background worker — no content script spam needed.

async function generateAndPushToken(forceOpen = false, action = "IMAGE_GENERATION") {
    const tabId = await findFlowTab();
    if (!tabId) {
        if (forceOpen) {
            console.log("⚠️  [OBSCURA v6] No Flow tab found. Auto-opening...");
            await autoOpenFlowTab();
        } else {
            console.log("⚠️  [OBSCURA v6] No Flow tab found. Heartbeat skipped (no forceOpen).");
        }
        return;
    }

    try {
        // Foreground/activate tab to prevent background reCAPTCHA throttling/telemetry flagging
        try {
            const tab = await chrome.tabs.get(tabId);
            if (tab) {
                await chrome.tabs.update(tabId, { active: true });
                await chrome.windows.update(tab.windowId, { focused: true, state: "normal" });
                console.log(`👁️ [OBSCURA v6] Activated Flow tab ${tabId} in window ${tab.windowId} and restored window state.`);
                await sleep(3000); // 3000ms delay to let the page wake up
            }
        } catch (e) {
            console.log("⚠️  [OBSCURA v6] Failed to foreground tab:", e.message);
        }

        const results = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            args: [ action ],
            func: async (action) => {
                try {
                    // ── Step 1: Bearer token ──
                    const authReq = await fetch("/fx/api/auth/session", { credentials: "include" });
                    if (!authReq.ok) return { error: "Auth fetch failed: " + authReq.status };
                    const auth = await authReq.json();
                    if (!auth.access_token) return { error: "No access_token in session" };

                    // ── Step 2: Dynamic reCAPTCHA site-key (G-Labs technique) ──
                    let siteKey = null;

                    // Method A: Extract from grecaptcha internal config (deep scan)
                    let siteKeysFound = [];
                    let siteKeyMethod = "NONE";
                    let cfgDiag = "NOT_FOUND";
                    try {
                        if (typeof ___grecaptcha_cfg !== "undefined") {
                            const cfg = ___grecaptcha_cfg;
                            const clientKeys = cfg.clients ? Object.keys(cfg.clients) : [];
                            cfgDiag = `clients=${clientKeys.length},keys=[${clientKeys.join(",")}]`;
                            
                            // Deep scan: walk 4 levels deep to find any sitekey property
                            const walk = (obj, depth, path) => {
                                if (!obj || typeof obj !== "object" || depth > 4) return;
                                for (const k of Object.keys(obj)) {
                                    try {
                                        const v = obj[k];
                                        if (k === "sitekey" && typeof v === "string") {
                                            if (!siteKeysFound.includes(v)) {
                                                siteKeysFound.push(v);
                                                console.log(`🔍 [OBSCURA v6] Found sitekey at ${path}.${k}: ${v}`);
                                            }
                                        } else if (v && typeof v === "object") {
                                            walk(v, depth + 1, `${path}.${k}`);
                                        }
                                    } catch (e) {}
                                }
                            };
                            
                            if (cfg.clients) {
                                for (const ckey of clientKeys) {
                                    walk(cfg.clients[ckey], 0, `clients[${ckey}]`);
                                }
                            }
                            
                            if (siteKeysFound.length > 0) {
                                siteKey = siteKeysFound[0];
                                siteKeyMethod = "A_CFG";
                            }
                        }
                    } catch (e) {
                        cfgDiag = "ERROR:" + e.message;
                    }

                    // Method B: Extract from script tags
                    if (!siteKey) {
                        try {
                            const scripts = document.querySelectorAll('script[src*="recaptcha"]');
                            for (const el of scripts) {
                                const m = el.src.match(/[?&]render=([^&]+)/);
                                if (m && m[1] !== "explicit") {
                                    siteKey = m[1];
                                    siteKeyMethod = "B_SCRIPT";
                                    break;
                                }
                            }
                        } catch (e) {}
                    }

                    // Method C: Hardcoded fallback removed for security.
                    if (!siteKey) {
                        console.error("🔍 [OBSCURA v6] Failed to resolve siteKey dynamically. Extension functionality may be limited.");
                        siteKeyMethod = "FAILED";
                    }
                    
                    console.log(`🔍 [OBSCURA v6] siteKey resolved via ${siteKeyMethod}. cfgDiag=${cfgDiag}. allKeys=[${siteKeysFound.join(",")}]`);

                    // Helper to simulate basic human interactions and generate telemetry
                    const simulateUserTelemetry = async () => {
                        try {
                            const start = Date.now();
                            while (Date.now() - start < 4000) {
                                const x = Math.floor(Math.random() * window.innerWidth);
                                const y = Math.floor(Math.random() * window.innerHeight);
                                const moveEvent = new MouseEvent("mousemove", {
                                    clientX: x,
                                    clientY: y,
                                    bubbles: true,
                                    cancelable: true
                                });
                                document.dispatchEvent(moveEvent);
                                
                                if (Math.random() > 0.8) {
                                    window.scrollBy(0, Math.random() > 0.5 ? 5 : -5);
                                }
                                await new Promise(r => setTimeout(r, 100));
                            }
                            const clickEvent = new MouseEvent("click", {
                                clientX: Math.floor(Math.random() * 100),
                                clientY: Math.floor(Math.random() * 100),
                                bubbles: true,
                                cancelable: true
                            });
                            document.body.dispatchEvent(clickEvent);
                            console.log("⚡ [OBSCURA v6] Simulated extended user telemetry.");
                        } catch (err) {
                            console.log("⚠️ [OBSCURA v6] Telemetry simulation error:", err);
                        }
                    };

                    // ── Step 3: Generate reCAPTCHA token ──
                    let recaptchaToken = "NONE";
                    if (typeof grecaptcha !== "undefined" && grecaptcha.enterprise) {
                        await simulateUserTelemetry();
                        await new Promise(r => grecaptcha.enterprise.ready(r));
                        recaptchaToken = await grecaptcha.enterprise.execute(siteKey, {
                            action: action
                        });
                    }

                    const pid = window.location.href.split('/project/')[1]?.split('/')[0] || "NOT_FOUND";
                    
                    return {
                        bearer: auth.access_token,
                        recaptcha: recaptchaToken,
                        user: auth.user?.name || "unknown",
                        siteKey: siteKey,
                        siteKeyMethod: siteKeyMethod,
                        cfgDiag: cfgDiag,
                        allSiteKeys: siteKeysFound,
                        projectId: pid,
                        action: action
                    };
                } catch (e) {
                    return { error: e.message || String(e) };
                }
            }
        });

        if (results && results[0] && results[0].result) {
            const data = results[0].result;

            if (data.error) {
                console.log("❌ [OBSCURA v6] Token gen failed:", data.error);
                return;
            }

            // Push to bridge
            const pushResp = await fetch(`${BRIDGE_URL}/push`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            if (pushResp.ok) {
                tokenCount++;
                lastPush = Date.now();
                chrome.storage.local.set({ tokenCount, lastPush });
                console.log(`✅ [OBSCURA v6] Fresh token #${tokenCount} pushed.`);
            }
        }
    } catch (e) {
        console.log("⚠️  [OBSCURA v6] Script injection failed:", e.message);
    }
}

// ─── 4. TAB MANAGEMENT ──────────────────────────────────────────

async function findFlowTab() {
    try {
        const tabs = await chrome.tabs.query({});
        // Priority 1: Flow project page
        const flowTabs = tabs.filter(t =>
            t.url && (
                t.url.includes("/tools/flow") ||
                (t.url.includes("labs.google/fx") && !t.url.includes("accounts.google.com"))
            )
        );
        if (flowTabs.length > 0) return flowTabs[0].id;

        // Priority 2: Any labs.google page
        const labsTabs = tabs.filter(t =>
            t.url && t.url.includes("labs.google") && !t.url.includes("accounts.google.com")
        );
        if (labsTabs.length > 0) return labsTabs[0].id;

        return null;
    } catch (e) {
        return null;
    }
}

async function autoOpenFlowTab() {
    try {
        const tab = await chrome.tabs.create({
            url: "https://labs.google/fx/tools/flow",
            active: false
        });

        // Wait for tab to fully load (max 15s)
        await new Promise(resolve => {
            const listener = (id, info) => {
                if (id === tab.id && info.status === "complete") {
                    chrome.tabs.onUpdated.removeListener(listener);
                    resolve();
                }
            };
            chrome.tabs.onUpdated.addListener(listener);
            setTimeout(() => {
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }, 15000);
        });

        console.log("🌐 [OBSCURA v6] Auto-opened Flow tab.");
    } catch (e) {
        console.log("⚠️  [OBSCURA v6] Failed to auto-open tab:", e.message);
    }
}

// ─── 5. UTILITY ──────────────────────────────────────────────────

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── 6. IN-BROWSER GENERATION ROUTING ────────────────────────────

async function generateVideoInBrowser(genData) {
    const tabId = await findFlowTab();
    if (!tabId) {
        console.log("⚠️ [OBSCURA v6] No Flow tab found for in-browser video generation.");
        await fetch(`${BRIDGE_URL}/push-generation-result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ error: "no active Google Flow tab found in Chrome" })
        });
        return;
    }

    try {
        // Step 1: Foreground the tab
        try {
            const tab = await chrome.tabs.get(tabId);
            if (tab) {
                await chrome.tabs.update(tabId, { active: true });
                await chrome.windows.update(tab.windowId, { focused: true, state: "normal" });
                console.log(`👁️ [OBSCURA v6] Activated Flow tab ${tabId} for video generation.`);
                await sleep(2000);
            }
        } catch (e) {}

        // Step 2: Generate reCAPTCHA token using IMAGE_GENERATION (always active and high score since tab is focused)
        const authResults = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            func: async () => {
                try {
                    const authReq = await fetch("/fx/api/auth/session", { credentials: "include" });
                    if (!authReq.ok) return { error: "Auth fetch failed: " + authReq.status };
                    const auth = await authReq.json();
                    
                    let siteKey = "";
                    if (typeof ___grecaptcha_cfg !== "undefined" && ___grecaptcha_cfg.clients) {
                        const clients = ___grecaptcha_cfg.clients;
                        for (const key of Object.keys(clients)) {
                            const client = clients[key];
                            for (const prop of Object.keys(client)) {
                                const val = client[prop];
                                if (val && typeof val === "object") {
                                    for (const p2 of Object.keys(val)) {
                                        const v2 = val[p2];
                                        if (v2 && typeof v2 === "object" && v2.sitekey) {
                                            siteKey = v2.sitekey;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                    const pid = window.location.href.split('/project/')[1]?.split('/')[0] || "NOT_FOUND";
                    return { bearer: auth.access_token, siteKey: siteKey, projectId: pid };
                } catch (e) {
                    return { error: e.message || String(e) };
                }
            }
        });

        if (!authResults || !authResults[0] || !authResults[0].result || authResults[0].result.error) {
            throw new Error(authResults?.[0]?.result?.error || "failed to retrieve auth session");
        }

        const { bearer, siteKey, projectId } = authResults[0].result;

        // Execute telemetry simulation inside page
        await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            func: async () => {
                try {
                    const start = Date.now();
                    while (Date.now() - start < 3000) {
                        const x = Math.floor(Math.random() * window.innerWidth);
                        const y = Math.floor(Math.random() * window.innerHeight);
                        const moveEvent = new MouseEvent("mousemove", { clientX: x, clientY: y, bubbles: true, cancelable: true });
                        document.dispatchEvent(moveEvent);
                        if (Math.random() > 0.8) {
                            window.scrollBy(0, Math.random() > 0.5 ? 5 : -5);
                        }
                        await new Promise(r => setTimeout(r, 100));
                    }
                    const clickEvent = new MouseEvent("click", { clientX: 10, clientY: 10, bubbles: true, cancelable: true });
                    document.body.dispatchEvent(clickEvent);
                    console.log("⚡ [OBSCURA v6] Simulated video telemetry.");
                } catch (e) {}
            }
        });

        // Generate reCAPTCHA token inside page
        const rcResult = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            args: [ siteKey, genData.action || "VIDEO_GENERATION" ],
            func: async (siteKey, reqAction) => {
                if (typeof grecaptcha !== "undefined" && grecaptcha.enterprise) {
                    await new Promise(r => grecaptcha.enterprise.ready(r));
                    return await grecaptcha.enterprise.execute(siteKey, { action: reqAction });
                }
                return "NONE";
            }
        });

        const recaptcha = rcResult?.[0]?.result || "NONE";

        // Step 3: Run the fetch call inside the page context
        console.log("🚀 [OBSCURA v6] Launching fetch inside page context...");
        const apiResults = await chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            args: [ bearer, recaptcha, projectId, genData ],
            func: async (bearer, recaptcha, projectId, genData) => {
                try {
                    const payload = {
                        "mediaGenerationContext": {
                            "batchId": crypto.randomUUID ? crypto.randomUUID() : "a0f095d8-c26a-4731-8bd9-79e6d59754b1",
                            "audioFailurePreference": "BLOCK_SILENCED_VIDEOS"
                        },
                        "clientContext": {
                            "projectId": projectId,
                            "tool": "PINHOLE",
                            "userPaygateTier": "PAYGATE_TIER_ONE",
                            "sessionId": ";" + Date.now(),
                            "recaptchaContext": {
                                "token": recaptcha,
                                "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                            }
                        },
                        "requests": [{
                            "aspectRatio": genData.aspectRatio,
                            "videoModelKey": "veo_3_1_t2v_lite",
                            "seed": Math.floor(Math.random() * 999999),
                            "textInput": {
                                "structuredPrompt": {
                                    "parts": [{"text": genData.prompt}]
                                }
                            },
                            "metadata": {}
                        }],
                        "useV2ModelConfig": true
                    };
                    
                    const resp = await fetch("https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText", {
                        method: "POST",
                        headers: {
                            "Authorization": "Bearer " + bearer,
                            "Content-Type": "text/plain;charset=UTF-8",
                            "Referer": "https://labs.google/"
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    if (!resp.ok) {
                        return { error: `HTTP ${resp.status}: ${await resp.text()}` };
                    }
                    return await resp.json();
                } catch (err) {
                    return { error: err.message || String(err) };
                }
            }
        });

        const apiResponse = apiResults?.[0]?.result || { error: "failed to execute API call on page context" };
        console.log("📥 [OBSCURA v6] Received API response:", apiResponse);

        // Step 4: Push the response back to the bridge
        await fetch(`${BRIDGE_URL}/push-generation-result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(apiResponse)
        });

    } catch (e) {
        console.log("❌ [OBSCURA v6] In-browser generation failed:", e.message);
        await fetch(`${BRIDGE_URL}/push-generation-result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ error: e.message || String(e) })
        });
    }
}
