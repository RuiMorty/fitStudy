const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");

function parseDay() {
  const dayArg = process.argv.find((arg) => arg.startsWith("--day="));
  const day = Number(dayArg?.split("=")[1] || process.argv[2]);
  if (!Number.isInteger(day) || day < 1) {
    throw new Error("Usage: node scripts/prepare-xhs-publish.js --day=6");
  }
  return day;
}

function tryRun(cmd, args, input) {
  try {
    execFileSync(cmd, args, { input, stdio: input ? ["pipe", "ignore", "ignore"] : "ignore" });
    return true;
  } catch {
    return false;
  }
}

function main() {
  const day = parseDay();
  const dir = path.join(ROOT, "xhs", `day${String(day).padStart(2, "0")}`);
  if (!fs.existsSync(dir)) throw new Error(`Missing package: ${dir}`);

  const title = fs.readFileSync(path.join(dir, "title.txt"), "utf8").trim();
  const caption = fs.readFileSync(path.join(dir, "caption.txt"), "utf8").trim();
  const tags = fs.readFileSync(path.join(dir, "tags.txt"), "utf8").trim();
  const text = `${title}\n\n${caption}\n\n${tags}\n`;

  const copied = tryRun("pbcopy", [], text);
  const openedFolder = tryRun("open", [dir]);
  const openedPublish = tryRun("open", ["https://creator.xiaohongshu.com/publish/publish"]);

  console.log(
    JSON.stringify(
      {
        packageDir: dir,
        copiedToClipboard: copied,
        openedFolder,
        openedPublish,
        nextStep: "Upload cover.png and slide-*.png, paste copied text, review, publish manually.",
      },
      null,
      2,
    ),
  );
}

main();
