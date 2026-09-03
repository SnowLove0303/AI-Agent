#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const NOTION_VERSION = process.env.NOTION_VERSION || "2022-06-28";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function usage() {
  return `Usage:
  node publish-note-to-notion.mjs --title "Juya AI 2026-05-19 BV..." --bvid BV... --note note.md --transcript BV..._transcript.txt

Options:
  --database <id>       Notion database id. Defaults to NOTION_DATABASE_ID or BILIBILI_DAILY_NOTION_DATABASE_ID.
  --page-id <id>        Update an existing Notion page instead of creating a new page.
  --title <text>        Page title.
  --bvid <id>           Bilibili BV id.
  --video-url <url>     Original Bilibili URL.
  --author <name>       Video author/uploader.
  --date <YYYY-MM-DD>   Report date.
  --note <path>         Generated markdown note path.
  --transcript <path>   Transcript text path.
  --dry-run             Print the planned page payload summary without calling Notion.

Token:
  Set one of NOTION_TOKEN, NOTION_KEY, or NOTION_API_KEY.`;
}

function readText(filePath) {
  if (!filePath) return "";
  const resolved = path.resolve(filePath);
  if (!fs.existsSync(resolved)) {
    throw new Error(`File not found: ${resolved}`);
  }
  const buffer = fs.readFileSync(resolved);
  if (buffer.length >= 2 && buffer[0] === 0xff && buffer[1] === 0xfe) {
    return buffer.toString("utf16le").replace(/^\uFEFF/, "");
  }
  return buffer.toString("utf8").replace(/^\uFEFF/, "");
}

function textChunks(text, limit = 1800) {
  const clean = String(text || "").replace(/\r\n/g, "\n").trim();
  if (!clean) return [];
  const chunks = [];
  let remaining = clean;
  while (remaining.length > limit) {
    let cut = remaining.lastIndexOf("\n\n", limit);
    if (cut < limit * 0.45) cut = remaining.lastIndexOf("\n", limit);
    if (cut < limit * 0.45) cut = limit;
    chunks.push(remaining.slice(0, cut).trim());
    remaining = remaining.slice(cut).trim();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

function richText(text) {
  return [{ type: "text", text: { content: String(text || "").slice(0, 2000) } }];
}

function heading(text, level = 2) {
  const type = level === 3 ? "heading_3" : "heading_2";
  return { object: "block", type, [type]: { rich_text: richText(text) } };
}

function paragraph(text) {
  return { object: "block", type: "paragraph", paragraph: { rich_text: richText(text) } };
}

function bullet(text) {
  return { object: "block", type: "bulleted_list_item", bulleted_list_item: { rich_text: richText(text) } };
}

function code(text, language = "plain text") {
  return {
    object: "block",
    type: "code",
    code: {
      rich_text: richText(text),
      language,
    },
  };
}

function makeBlocks(args, noteText, transcriptText) {
  const blocks = [heading("Source", 2)];
  if (args.bvid) blocks.push(bullet(`BV: ${args.bvid}`));
  if (args.videoUrl) blocks.push(bullet(`Video: ${args.videoUrl}`));
  if (args.author) blocks.push(bullet(`Author: ${args.author}`));
  if (args.date) blocks.push(bullet(`Date: ${args.date}`));

  if (noteText.trim()) {
    blocks.push(heading("Daily Note", 2));
    for (const chunk of textChunks(noteText, 1800)) {
      blocks.push(code(chunk, "markdown"));
    }
  }

  if (transcriptText.trim()) {
    blocks.push(heading("Transcript", 2));
    for (const chunk of textChunks(transcriptText, 1800)) {
      blocks.push(paragraph(chunk));
    }
  }

  if (!noteText.trim() && !transcriptText.trim()) {
    blocks.push(paragraph("No note or transcript content was provided."));
  }

  return blocks;
}

function getToken() {
  return process.env.NOTION_TOKEN || process.env.NOTION_KEY || process.env.NOTION_API_KEY || "";
}

async function notion(method, endpoint, body, token) {
  const response = await fetch(`https://api.notion.com/v1${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "Notion-Version": NOTION_VERSION,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }
  if (!response.ok) {
    throw new Error(`Notion ${method} ${endpoint} failed: ${response.status} ${JSON.stringify(data)}`);
  }
  return data;
}

async function getTitleProperty(databaseId, token) {
  const database = await notion("GET", `/databases/${databaseId}`, null, token);
  for (const [name, property] of Object.entries(database.properties || {})) {
    if (property.type === "title") return name;
  }
  throw new Error(`No title property found in Notion database: ${databaseId}`);
}

async function appendBlocks(pageId, blocks, token) {
  for (let index = 0; index < blocks.length; index += 90) {
    const children = blocks.slice(index, index + 90);
    await notion("PATCH", `/blocks/${pageId}/children`, { children }, token);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h) {
    console.log(usage());
    return;
  }

  const databaseId = args.database || process.env.NOTION_DATABASE_ID || process.env.BILIBILI_DAILY_NOTION_DATABASE_ID || "";
  const targetPageId = args.pageId || process.env.NOTION_PAGE_ID || process.env.BILIBILI_DAILY_NOTION_PAGE_ID || "";
  const title = args.title || [args.author, args.date, args.bvid].filter(Boolean).join(" ") || "Bilibili Daily Note";
  const noteText = readText(args.note);
  const transcriptText = readText(args.transcript);
  const blocks = makeBlocks(args, noteText, transcriptText);

  if (args.dryRun) {
    console.log(JSON.stringify({
      dry_run: true,
      title,
      database_id: databaseId || null,
      target_page_id: targetPageId || null,
      note_chars: noteText.length,
      transcript_chars: transcriptText.length,
      block_count: blocks.length,
    }, null, 2));
    return;
  }

  const token = getToken();
  if (!token) throw new Error("Missing Notion token. Set NOTION_TOKEN, NOTION_KEY, or NOTION_API_KEY.");
  if (!targetPageId && !databaseId) {
    throw new Error("Missing Notion database. Set --database, NOTION_DATABASE_ID, or BILIBILI_DAILY_NOTION_DATABASE_ID.");
  }

  let pageId = targetPageId;
  let pageUrl = "";
  if (!pageId) {
    const titleProperty = await getTitleProperty(databaseId, token);
    const page = await notion("POST", "/pages", {
      parent: { database_id: databaseId },
      properties: {
        [titleProperty]: {
          title: richText(title),
        },
      },
    }, token);
    pageId = page.id;
    pageUrl = page.url;
  } else {
    pageUrl = `https://www.notion.so/${pageId.replace(/-/g, "")}`;
  }

  await appendBlocks(pageId, blocks, token);
  console.log(JSON.stringify({
    ok: true,
    page_id: pageId,
    page_url: pageUrl || `https://www.notion.so/${pageId.replace(/-/g, "")}`,
    block_count: blocks.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
