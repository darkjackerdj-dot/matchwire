const SOURCES = [
  {
    name: "BBC Sport",
    url: "https://feeds.bbci.co.uk/sport/football/rss.xml",
  },
  {
    name: "ESPN",
    url: "https://www.espn.com/espn/rss/soccer/news",
  },
  {
    name: "The Guardian",
    url: "https://www.theguardian.com/football/rss",
  },
];

const MAX_ARTICLES_PER_SOURCE = 20;
const MAX_SEND_PER_RUN = 10;

const CHANNEL_USERNAME = "@matchwirenews";
const CHANNEL_URL = "https://t.me/matchwirenews";

const RUMOUR_WORDS = [
  "rumour",
  "rumor",
  "reportedly",
  "reports suggest",
  "reports claim",
  "could join",
  "could leave",
  "could move",
  "may join",
  "may leave",
  "might join",
  "might leave",
  "interested in",
  "interest in",
  "linked with",
  "linked to",
  "eyeing",
  "considering",
  "targeting",
];

const LOW_VALUE_WORDS = [
  "prediction",
  "predictions",
  "opinion",
  "analysis",
  "editorial",
  "quiz",
  "team of the week",
  "player of the week",
  "power rankings",
  "ratings",
  "ranking",
  "rankings",
  "highlights",
  "all the goals",
  "five things",
  "things to know",
  "key questions",
  "questions answered",
  "everything you need to know",
  "all you need to know",
  "what are the premier league rules",
  "how does it work",
  "how do",
  "how does",
];

const FOOTBALL_WORDS = [
  "football",
  "soccer",
  "premier league",
  "champions league",
  "europa league",
  "conference league",
  "world cup",
  "fa cup",
  "league cup",
  "la liga",
  "bundesliga",
  "serie a",
  "ligue 1",
  "arsenal",
  "chelsea",
  "liverpool",
  "manchester united",
  "manchester city",
  "tottenham",
  "newcastle",
  "aston villa",
  "everton",
  "west ham",
  "brighton",
  "fulham",
  "crystal palace",
  "nottingham forest",
  "wolves",
  "bournemouth",
  "brentford",
  "leeds",
  "sunderland",
  "real madrid",
  "barcelona",
  "atletico madrid",
  "bayern",
  "borussia dortmund",
  "psg",
  "paris saint-germain",
  "juventus",
  "inter milan",
  "ac milan",
  "napoli",
  "roma",
  "santos",
  "neymar",
  "manager",
  "coach",
  "player",
  "players",
  "striker",
  "midfielder",
  "defender",
  "goalkeeper",
  "referee",
  "var",
  "transfer",
  "transfers",
  "injury",
  "injured",
  "squad",
  "match",
  "goal",
  "goals",
];

function normalize(text) {
  return text
    .toLowerCase()
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function decodeHtml(text) {
  return text
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/gi, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&apos;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
}

function extractTag(block, tag) {
  const regex = new RegExp(
    `<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tag}>`,
    "i"
  );

  const match = block.match(regex);
  return match ? decodeHtml(match[1]).trim() : "";
}

function isRumour(title) {
  const text = normalize(title);
  return RUMOUR_WORDS.some((word) => text.includes(word));
}

function isGoodNews(title) {
  const text = normalize(title);

  if (!FOOTBALL_WORDS.some((word) => text.includes(word))) {
    return false;
  }

  if (LOW_VALUE_WORDS.some((word) => text.includes(word))) {
    return false;
  }

  return true;
}

function hashString(text) {
  let hash = 2166136261;

  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }

  return ("00000000" + (hash >>> 0).toString(16)).slice(-8);
}

function extractImage(item) {
  // RSS media:content
  const mediaContent =
    item.match(/<media:content[^>]+url=["']([^"']+)["']/i);

  if (mediaContent) {
    return mediaContent[1];
  }

  // RSS media:thumbnail
  const mediaThumbnail =
    item.match(/<media:thumbnail[^>]+url=["']([^"']+)["']/i);

  if (mediaThumbnail) {
    return mediaThumbnail[1];
  }

  // RSS enclosure image
  const enclosure =
    item.match(
      /<enclosure[^>]+url=["']([^"']+)["'][^>]+type=["']image\/[^"']+["']/i
    );

  if (enclosure) {
    return enclosure[1];
  }

  // Some feeds put the image URL inside the description/content
  const imageInContent =
    item.match(
      /<img[^>]+src=["']([^"']+)["']/i
    );

  if (imageInContent) {
    return imageInContent[1];
  }

  return null;
}

async function fetchFeed(source) {
  try {
    const response = await fetch(source.url, {
      headers: {
        "User-Agent": "Matchwire/1.0 Football News Bot",
      },
    });

    if (!response.ok) {
      console.log(`${source.name}: HTTP ${response.status}`);
      return [];
    }

    const xml = await response.text();

    const items = xml.match(/<item[\s\S]*?<\/item>/gi) || [];

    const articles = [];

    for (const item of items.slice(0, MAX_ARTICLES_PER_SOURCE)) {
      const title = extractTag(item, "title");
      const link = extractTag(item, "link");
      const published =
        extractTag(item, "pubDate") ||
        extractTag(item, "published") ||
        extractTag(item, "updated");

      if (!title || !link) {
        continue;
      }

      if (!isGoodNews(title)) {
        continue;
      }

      articles.push({
        title,
        link,
        published,
        source: source.name,
        rumour: isRumour(title),
        image: extractImage(item),
      });
    }

    return articles;
  } catch (error) {
    console.log(`${source.name}: ${error}`);
    return [];
  }
}

async function collectNews() {
  const results = [];

  for (const source of SOURCES) {
    const articles = await fetchFeed(source);

    console.log(
      `${source.name}: ${articles.length} usable articles`
    );

    results.push(...articles);
  }

  return results;
}

function deduplicateArticles(articles) {
  const seen = new Set();
  const unique = [];

  for (const article of articles) {
    const key = normalize(article.title)
      .replace(/[^a-z0-9 ]/g, "")
      .trim();

    if (!key || seen.has(key)) {
      continue;
    }

    seen.add(key);
    unique.push(article);
  }

  return unique;
}

async function telegram(env, method, body) {
  const response = await fetch(
    `https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    }
  );

  return response.json();
}

function escapeMarkdown(text) {
  return text.replace(/([_*[\]()~`>#+\-=|{}.!])/g, "\\$1");
}

async function sendArticle(env, chatId, article) {
  const header = article.rumour
    ? "⚠️ *MATCHWIRE — RUMOUR*"
    : "⚽ *MATCHWIRE FOOTBALL UPDATE*";

  const caption =
    `${header}\n\n` +
    `📰 *${escapeMarkdown(article.title)}*\n\n` +
    `🌐 Source: ${escapeMarkdown(article.source)}\n\n` +
    `🔗 [READ FULL STORY](${article.link})`;

  // Use the article thumbnail when the RSS feed provides one
  if (article.image) {
    try {
      const photoResult = await telegram(env, "sendPhoto", {
        chat_id: chatId,
        photo: article.image,
        caption,
        parse_mode: "Markdown",
      });

      if (photoResult.ok) {
        return photoResult;
      }

      console.log(
        `Thumbnail failed for ${article.source}: ${photoResult.description}`
      );
    } catch (error) {
      console.log(
        `Thumbnail error for ${article.source}: ${error}`
      );
    }
  }

  // Fallback: send the normal text message
  return telegram(env, "sendMessage", {
    chat_id: chatId,
    text: caption,
    parse_mode: "Markdown",
    disable_web_page_preview: false,
  });
}


async function getSubscribers(env) {
  const data = await env.MATCHWIRE_KV.get("subscribers");

  if (!data) {
    return [];
  }

  try {
    return JSON.parse(data);
  } catch {
    return [];
  }
}

async function saveSubscribers(env, subscribers) {
  await env.MATCHWIRE_KV.put(
    "subscribers",
    JSON.stringify(subscribers)
  );
}

async function getSeenNews(env) {
  const data = await env.MATCHWIRE_KV.get("seen_news");

  if (!data) {
    return [];
  }

  try {
    return JSON.parse(data);
  } catch {
    return [];
  }
}

async function saveSeenNews(env, seen) {
  const trimmed = seen.slice(-500);

  await env.MATCHWIRE_KV.put(
    "seen_news",
    JSON.stringify(trimmed)
  );
}

async function processNews(env) {
  console.log("=================================");
  console.log("MATCHWIRE NEWS CHECK");
  console.log("=================================");

  const subscribers = await getSubscribers(env);

  if (subscribers.length === 0) {
    console.log("No active subscribers.");
  }

  const seenNews = await getSeenNews(env);
  const seenSet = new Set(seenNews);

  let articles = await collectNews();

  articles = deduplicateArticles(articles);

  console.log(`Unique articles: ${articles.length}`);

  const newArticles = [];

  for (const article of articles) {
    const key = hashString(
      normalize(article.title) + "|" + article.link
    );

    if (seenSet.has(key)) {
      continue;
    }

    newArticles.push({
      ...article,
      key,
    });
  }

  console.log(`New articles: ${newArticles.length}`);

  const toSend = newArticles.slice(0, MAX_SEND_PER_RUN);

  for (const article of toSend) {
    let channelSent = false;

    // Post to the official Matchwire News channel
    try {
      const channelResult = await sendArticle(
        env,
        CHANNEL_USERNAME,
        article
      );

      if (channelResult.ok) {
        channelSent = true;
        console.log(
          `Channel post sent: ${article.title}`
        );
      } else {
        console.log(
          `Channel send failed: ${channelResult.description}`
        );
      }
    } catch (error) {
      console.log(
        `Channel Telegram error: ${error}`
      );
    }

    // Send to active bot subscribers
    for (const chatId of subscribers) {
      try {
        const result = await sendArticle(
          env,
          chatId,
          article
        );

        if (!result.ok) {
          console.log(
            `Telegram send failed for ${chatId}: ${result.description}`
          );
        }
      } catch (error) {
        console.log(
          `Telegram error for ${chatId}: ${error}`
        );
      }
    }

    // Mark as seen only after successful channel posting
    if (channelSent) {
      seenSet.add(article.key);
    }
  }

  await saveSeenNews(env, Array.from(seenSet));

  console.log("MATCHWIRE CHECK COMPLETE");
}


async function checkChannelMembership(env, userId) {
  const result = await telegram(env, "getChatMember", {
    chat_id: CHANNEL_USERNAME,
    user_id: userId,
  });

  if (!result.ok || !result.result) {
    console.log(
      `Membership check failed for ${userId}: ${
        result.description || "unknown error"
      }`
    );
    return false;
  }

  const member = result.result;

  return (
    member.status === "creator" ||
    member.status === "administrator" ||
    member.status === "member" ||
    (member.status === "restricted" && member.is_member === true)
  );
}

async function activateSubscriber(env, chatId) {
  const subscribers = await getSubscribers(env);

  if (!subscribers.includes(chatId)) {
    subscribers.push(chatId);
    await saveSubscribers(env, subscribers);
  }
}

async function sendJoinMessage(env, chatId) {
  return telegram(env, "sendMessage", {
    chat_id: chatId,
    text: `⚽ *MATCHWIRE*

To use Matchwire football news alerts, please join our official news channel first.

After joining, tap *I've Joined* and we'll verify your membership.`,
    parse_mode: "Markdown",
    reply_markup: {
      inline_keyboard: [
        [
          {
            text: "📢 JOIN MATCHWIRE NEWS",
            url: CHANNEL_URL,
          },
        ],
        [
          {
            text: "✅ I'VE JOINED",
            callback_data: "verify_join",
          },
        ],
      ],
    },
  });
}

async function handleStart(env, chatId) {
  const isMember = await checkChannelMembership(env, chatId);

  if (!isMember) {
    return sendJoinMessage(env, chatId);
  }

  await activateSubscriber(env, chatId);

  return telegram(env, "sendMessage", {
    chat_id: chatId,
    text: `🟢 *MATCHWIRE UPDATES STARTED!*

You are subscribed to automatic football news alerts.

Use /stop to stop updates.`,
    parse_mode: "Markdown",
  });
}

async function handleStop(env, chatId) {
  const subscribers = await getSubscribers(env);

  const updated = subscribers.filter(
    (id) => id !== chatId
  );

  await saveSubscribers(env, updated);

  return telegram(env, "sendMessage", {
    chat_id: chatId,
    text:
      "🔴 *MATCHWIRE UPDATES STOPPED.*\n\n" +
      "Use /start to activate updates again.",
    parse_mode: "Markdown",
  });
}



export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response(
        "⚽ MATCHWIRE is online.",
        { status: 200 }
      );
    }

    try {
      const update = await request.json();

      if (update.callback_query) {
        const callback = update.callback_query;
        const userId = callback.from.id;
        const chatId = callback.message?.chat?.id;

        if (callback.data === "verify_join" && chatId) {
          const isMember = await checkChannelMembership(env, userId);

          if (isMember) {
            await activateSubscriber(env, chatId);

            await telegram(env, "answerCallbackQuery", {
              callback_query_id: callback.id,
              text: "✅ Membership verified!",
            });

            await telegram(env, "sendMessage", {
              chat_id: chatId,
              text: `🟢 *MATCHWIRE UPDATES STARTED!*

Membership verified successfully.
You will now receive automatic football news alerts.

Use /stop to stop updates.`,
              parse_mode: "Markdown",
            });
          } else {
            await telegram(env, "answerCallbackQuery", {
              callback_query_id: callback.id,
              text: "❌ Please join the channel first.",
              show_alert: true,
            });
          }
        }
      }

      if (update.message) {
        const chatId = update.message.chat.id;
        const text = (update.message.text || "").trim();

        if (text === "/start") {
          await handleStart(env, chatId);
        }

        if (text === "/stop") {
          await handleStop(env, chatId);
        }

        if (text === "/help") {
          await telegram(env, "sendMessage", {
            chat_id: chatId,
            text:
              "⚽ *MATCHWIRE — FOOTBALL NEWS ALERTS*\n\n" +
              "📰 Reliable football news from trusted sources.\n" +
              "🌍 Premier League & global football coverage.\n" +
              "🔗 Direct links to full stories.\n" +
              "⚠️ Rumours are clearly labelled.\n\n" +
              "*Commands:*\n" +
              "/start — Activate football news alerts\n" +
              "/stop — Stop automatic alerts\n" +
              "/help — Show this help message\n\n" +
              "📢 Official Channel: @matchwirenews",
            parse_mode: "Markdown",
          });
        }

      }

      return new Response("OK");
    } catch (error) {
      console.log(`Webhook error: ${error}`);

      return new Response("OK");
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(processNews(env));
  },
};
