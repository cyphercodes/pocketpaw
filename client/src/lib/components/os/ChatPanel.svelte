<!-- ChatPanel.svelte — Full-viewport Chat tab with session history sidebar.
     Updated: 2026-03-25 — Added Agents section in sidebar (virtual C-suite team: CFO, CMO, COO, CISO).
     Click an agent to start a 1:1 conversation with that specific soul.
-->
<script lang="ts">
  import { onMount, tick } from "svelte";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import Mic from "@lucide/svelte/icons/mic";
  import Video from "@lucide/svelte/icons/video";
  import Phone from "@lucide/svelte/icons/phone";
  import Plus from "@lucide/svelte/icons/plus";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import Search from "@lucide/svelte/icons/search";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Clock from "@lucide/svelte/icons/clock";
  import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";

  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Users from "@lucide/svelte/icons/users";
  import Hash from "@lucide/svelte/icons/hash";
  import Bot from "@lucide/svelte/icons/bot";
  import Circle from "@lucide/svelte/icons/circle";

  let { onClose }: { onClose: () => void } = $props();

  // --- Sidebar settings state ---
  let sidebarSettingsOpen = $state(false);
  let chatModel = $state<"claude" | "gpt4" | "gemini">("claude");
  let responseStyle = $state<"fast" | "balanced" | "deep">("balanced");
  let memoryEnabled = $state(true);
  let streamEnabled = $state(true);

  type Role = "user" | "agent";
  type Message = { id: string; role: Role; content: string; time: string; senderName?: string; senderColor?: string };

  // --- Unified contact system (humans + agents) ---
  type Contact = {
    id: string; name: string; initials: string; color: string;
    kind: "human" | "agent";
    status: "online" | "offline" | "typing" | "idle";
    lastMessage?: string; lastTime?: string;
    unread?: number;
  };

  type ChatSession = { id: string; title: string; time: string };
  type ChatRoom = {
    id: string; name: string; type: "dm" | "group" | "channel";
    members: Contact[]; lastMessage?: string; lastTime?: string;
    unread?: number; icon?: string;
    messages: Message[];
    sessions?: ChatSession[]; // multi-session for agents only
  };

  // --- Contacts ---
  const CONTACTS: Contact[] = [
    // Humans
    { id: "prakash", name: "Prakash", initials: "PG", color: "#0A84FF", kind: "human", status: "online" },
    { id: "robert", name: "Robert", initials: "RK", color: "#FF6B35", kind: "human", status: "online", lastMessage: "Let's prep the NexWrk deck", lastTime: "2m", unread: 2 },
    { id: "rohit", name: "Rohit", initials: "RS", color: "#30D158", kind: "human", status: "offline", lastMessage: "Ripple core extraction done", lastTime: "1h" },
    { id: "diana", name: "Diana", initials: "DR", color: "#E040FB", kind: "human", status: "online", lastMessage: "Saturday event staff confirmed", lastTime: "15m", unread: 1 },
    { id: "richie", name: "Richie", initials: "RR", color: "#FEBC2E", kind: "human", status: "offline", lastMessage: "NexWrk board meeting moved to Friday", lastTime: "3h" },
    // Agents
    { id: "pa", name: "PocketPaw", initials: "PA", color: "#BF5AF2", kind: "agent", status: "online", lastMessage: "Deployed the auth fix to staging", lastTime: "5m" },
    { id: "cfo", name: "CFO", initials: "CF", color: "#30D158", kind: "agent", status: "online", lastMessage: "Cash flow looks tight next week", lastTime: "12m" },
    { id: "cmo", name: "CMO", initials: "CM", color: "#0A84FF", kind: "agent", status: "online", lastMessage: "Guest reviews trending up +18%", lastTime: "20m" },
    { id: "coo", name: "COO", initials: "CO", color: "#FF9F0A", kind: "agent", status: "idle", lastMessage: "Saturday staff schedule updated", lastTime: "1h" },
    { id: "ciso", name: "CISO", initials: "CS", color: "#FF453A", kind: "agent", status: "idle", lastMessage: "Compliance check passed", lastTime: "3h" },
  ];

  // --- Rooms ---
  const ROOMS: ChatRoom[] = [
    // DMs — humans
    { id: "dm-robert", name: "Robert", type: "dm", members: [CONTACTS[1]], lastMessage: "Let's prep the NexWrk deck", lastTime: "2m", unread: 2, messages: [
      { id: "r1", role: "user", content: "How's the NexWrk pitch deck coming?", time: "10:30" },
      { id: "r2", role: "agent", content: "Let's prep the NexWrk deck — I've got the revenue numbers from CFO. Can you pull the venue photos?", time: "10:32", senderName: "Robert", senderColor: "#FF6B35" },
    ]},
    { id: "dm-diana", name: "Diana", type: "dm", members: [CONTACTS[3]], lastMessage: "Saturday event staff confirmed", lastTime: "15m", unread: 1, messages: [
      { id: "d1", role: "agent", content: "Saturday event staff confirmed — 6 people on floor, 2 bar, 1 AV. All good.", time: "11:15", senderName: "Diana", senderColor: "#E040FB" },
    ]},
    { id: "dm-rohit", name: "Rohit", type: "dm", members: [CONTACTS[2]], lastMessage: "Ripple core extraction done", lastTime: "1h", messages: [
      { id: "ro1", role: "agent", content: "Ripple core extraction done — @ripple/core is 4200 lines, zero framework deps. PR incoming.", time: "09:45", senderName: "Rohit", senderColor: "#30D158" },
    ]},
    { id: "dm-richie", name: "Richie", type: "dm", members: [CONTACTS[4]], lastMessage: "NexWrk board meeting moved to Friday", lastTime: "3h", messages: [] },
    // DMs — agents
    { id: "dm-pa", name: "PocketPaw", type: "dm", members: [CONTACTS[5]], lastMessage: "Deployed the auth fix to staging", lastTime: "5m", sessions: [
      { id: "pa-s1", title: "Competitive analysis setup", time: "Today" },
      { id: "pa-s2", title: "Soul Protocol spec review", time: "Today" },
      { id: "pa-s3", title: "Deploy fixes to staging", time: "Yesterday" },
    ], messages: [
      { id: "m1", role: "user", content: "Help me set up a competitive analysis workflow", time: "09:14" },
      { id: "m2", role: "agent", content: "I'll set up a complete competitive analysis workspace for you. Here's my plan:\n\n1. Research Setup\n  • Configure web search tool for competitor monitoring\n  • Set up scheduled searches for pricing changes\n\n2. Analysis Framework\n  • Build comparison templates\n  • Create a summary dashboard Pocket", time: "09:14" },
    ]},
    { id: "dm-cfo", name: "CFO", type: "dm", members: [CONTACTS[6]], lastMessage: "Cash flow looks tight next week", lastTime: "12m", sessions: [
      { id: "cfo-s1", title: "Weekly cash flow review", time: "Today" },
      { id: "cfo-s2", title: "Q1 revenue forecast", time: "Yesterday" },
    ], messages: [
      { id: "cf1", role: "agent", content: "Cash flow looks tight next week — $18K outgoing (venue rent + Diageo payment) against $14K confirmed revenue. Recommend holding the Apr 5 deposit until Thursday's event settles.", time: "11:00", senderName: "CFO", senderColor: "#30D158" },
    ]},
    // Groups
    { id: "g-csuite", name: "NexWrk C-Suite", type: "group", members: [CONTACTS[1], CONTACTS[3], CONTACTS[6], CONTACTS[7], CONTACTS[8], CONTACTS[9]], lastMessage: "CFO: Revenue forecast updated", lastTime: "8m", unread: 3, messages: [
      { id: "g1", role: "agent", content: "Revenue forecast updated — projecting $68K next week based on confirmed bookings.", time: "11:20", senderName: "CFO", senderColor: "#30D158" },
      { id: "g2", role: "agent", content: "Guest reviews trending up — 4.7★ average this week. 'Atmosphere' is the #1 theme.", time: "11:22", senderName: "CMO", senderColor: "#0A84FF" },
      { id: "g3", role: "agent", content: "Saturday AV setup needs sign-off. DJ contract is still unsigned.", time: "11:25", senderName: "COO", senderColor: "#FF9F0A" },
    ]},
    { id: "g-ops", name: "Operations", type: "group", members: [CONTACTS[0], CONTACTS[3], CONTACTS[8]], lastMessage: "Diana: Staff schedule locked", lastTime: "30m", messages: [
      { id: "o1", role: "agent", content: "Staff schedule locked for Saturday. 6 floor + 2 bar + 1 AV.", time: "10:50", senderName: "Diana", senderColor: "#E040FB" },
    ]},
    { id: "g-founders", name: "Founders", type: "group", members: [CONTACTS[0], CONTACTS[1], CONTACTS[4]], lastMessage: "Robert: Demo prep tomorrow?", lastTime: "2h", messages: [] },
    // Channels
    { id: "ch-general", name: "general", type: "channel", members: CONTACTS, lastMessage: "PocketPaw: v0.4.9 deployed", lastTime: "1h", messages: [] },
    { id: "ch-revenue", name: "revenue", type: "channel", members: [CONTACTS[0], CONTACTS[1], CONTACTS[6]], lastMessage: "CFO: March close at $142K", lastTime: "4h", messages: [] },
    { id: "ch-incidents", name: "incidents", type: "channel", members: [CONTACTS[0], CONTACTS[9]], lastMessage: "CISO: All clear — no alerts", lastTime: "6h", messages: [] },
  ];

  // --- Sidebar state ---
  let activeRoomId = $state<string>("dm-robert");
  let expandedRoomId = $state<string | null>(null);
  let searchQuery = $state("");
  let sectionOpen = $state<Record<string, boolean>>({ dms: true, groups: true, channels: true });

  function toggleSection(key: string) { sectionOpen[key] = !sectionOpen[key]; }

  let activeRoom = $derived(ROOMS.find(r => r.id === activeRoomId) || ROOMS[0]);
  let messages = $derived(activeRoom?.messages || []);

  let filteredRooms = $derived(
    searchQuery.trim() === ""
      ? ROOMS
      : ROOMS.filter(r =>
          r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (r.lastMessage || "").toLowerCase().includes(searchQuery.toLowerCase())
        )
  );

  let dmRooms = $derived(filteredRooms.filter(r => r.type === "dm"));
  let groupRooms = $derived(filteredRooms.filter(r => r.type === "group"));
  let channelRooms = $derived(filteredRooms.filter(r => r.type === "channel"));

  function nowTime() {
    return new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
  }

  let inputValue = $state("");
  let isTyping = $state(false);
  let messagesEl: HTMLDivElement | null = null;

  const MOCK_RESPONSES = [
    "Got it. I'm on it — I'll update you when this is done.",
    "Great idea. Let me research that and come back with a structured plan.",
    "Sure, I'll configure that right now. You should see the results in a few seconds.",
    "I've noted that. Want me to create a Pocket for this or add it to an existing one?",
    "Interesting. I'll analyze that and give you a detailed breakdown shortly.",
  ];

  async function scrollToBottom() {
    await tick();
    if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendMessage() {
    const text = inputValue.trim();
    if (!text || isTyping || !activeRoom) return;
    inputValue = "";

    activeRoom.messages = [...activeRoom.messages,
      { id: `m${Date.now()}`, role: "user", content: text, time: nowTime() },
    ];
    await scrollToBottom();

    isTyping = true;
    await scrollToBottom();
    await new Promise((r) => setTimeout(r, 800));

    // Pick a responder based on room type
    const responder = activeRoom.members[0];
    activeRoom.messages = [...activeRoom.messages, {
      id: `m${Date.now() + 1}`, role: "agent",
      content: MOCK_RESPONSES[Math.floor(Math.random() * MOCK_RESPONSES.length)],
      time: nowTime(),
      senderName: responder?.name,
      senderColor: responder?.color,
    }];
    isTyping = false;
    await scrollToBottom();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  function newChat() {
    // Create a new DM with PocketPaw
    const id = `dm-new-${Date.now()}`;
    const newRoom: ChatRoom = {
      id, name: "New Chat", type: "dm", members: [CONTACTS[5]], messages: [],
      lastMessage: "", lastTime: "Now",
    };
    ROOMS.unshift(newRoom);
    activeRoomId = id;
  }

  function renderMarkdown(text: string): string {
    const lines = text.split("\n");
    const out: string[] = [];
    for (const line of lines) {
      if (/^\s+[•·-]\s/.test(line)) { out.push(`<div class="md-bullet">${inlineMd(line.replace(/^\s+[•·-]\s/, ""))}</div>`); continue; }
      if (/^\d+\.\s/.test(line)) { out.push(`<div class="md-numbered">${inlineMd(line)}</div>`); continue; }
      if (line.trim() === "") { out.push('<div class="md-gap"></div>'); continue; }
      out.push(`<div class="md-line">${inlineMd(line)}</div>`);
    }
    return out.join("");
  }

  function inlineMd(text: string): string {
    return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  }

  // Resizable sidebar
  let sidebarW = $state(260);
  let sidebarDragging = $state(false);
  let sidebarDragStart = { mx: 0, w: 0 };
  function onSidebarResize(e: PointerEvent) {
    e.preventDefault();
    sidebarDragging = true;
    sidebarDragStart = { mx: e.clientX, w: sidebarW };
    window.addEventListener("pointermove", onSidebarMove);
    window.addEventListener("pointerup", onSidebarUp);
  }
  function onSidebarMove(e: PointerEvent) {
    sidebarW = Math.max(200, Math.min(400, sidebarDragStart.w + (e.clientX - sidebarDragStart.mx)));
  }
  function onSidebarUp() {
    sidebarDragging = false;
    window.removeEventListener("pointermove", onSidebarMove);
    window.removeEventListener("pointerup", onSidebarUp);
  }

  let visible = $state(false);
  onMount(() => { scrollToBottom(); requestAnimationFrame(() => { visible = true; }); });
</script>

<div class={visible ? "chat-panel chat-visible liquid-glass glass-noise" : "chat-panel liquid-glass glass-noise"}>
  <div class="chat-body">
    <!-- Unified chat sidebar — humans + agents + groups + channels -->
    <aside class="session-sidebar" style="width:{sidebarW}px">
      <!-- Header -->
      <div class="flex items-center gap-2 p-2.5 pb-1.5 shrink-0">
        <button class="flex items-center gap-1.5 w-full px-3 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] text-[#0A84FF] text-[13px] font-medium transition-colors" onclick={newChat}>
          <Plus size={14} strokeWidth={2} />
          <span>New Chat</span>
        </button>
      </div>

      <!-- Search -->
      <div class="flex items-center gap-2 mx-2.5 mb-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.04]">
        <Search size={13} strokeWidth={1.8} class="text-white/30 shrink-0" />
        <input
          class="flex-1 bg-transparent border-none outline-none text-[12px] text-white/80 placeholder:text-white/25"
          type="text" placeholder="Search..."
          bind:value={searchQuery} autocomplete="off" spellcheck="false"
        />
      </div>

      <!-- Room list -->
      <div class="flex-1 overflow-y-auto px-1.5 pb-2" style="scrollbar-width:none">
        <!-- DMs section -->
        <button class="flex items-center gap-1.5 w-full px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-white/30 hover:text-white/50 transition-colors" onclick={() => toggleSection("dms")}>
          <ChevronDown size={10} strokeWidth={2} class={sectionOpen.dms ? "" : "-rotate-90"} style="transition:transform 0.15s" />
          Direct Messages
        </button>
        {#if sectionOpen.dms}
          {#each dmRooms as room (room.id)}
            {@const contact = room.members[0]}
            {@const hasSessions = contact.kind === "agent" && room.sessions && room.sessions.length > 0}
            {@const isExpanded = expandedRoomId === room.id}
            <div class={room.id === activeRoomId ? 'bg-white/[0.05] rounded-lg' : ''}>
              <button
                class={`flex items-center gap-2.5 w-full px-2 py-[6px] rounded-lg text-left transition-colors hover:bg-white/[0.04]`}
                onclick={() => {
                  activeRoomId = room.id;
                  if (hasSessions) expandedRoomId = isExpanded ? null : room.id;
                }}
              >
                <!-- Avatar with status dot -->
                <div class="relative shrink-0">
                  <div class={`w-8 h-8 ${contact.kind === 'human' ? 'rounded-full' : 'rounded-lg'} flex items-center justify-center text-[10px] font-bold text-white tracking-tight`} style="background:{contact.color}; opacity:{contact.status === 'offline' || contact.status === 'idle' ? 0.5 : 1}">
                    {contact.initials}
                  </div>
                  {#if contact.kind === "agent"}
                    <div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[#1e1e1c] flex items-center justify-center">
                      <Bot size={8} strokeWidth={2} class="text-white/50" />
                    </div>
                  {:else if contact.status === "online"}
                    <div class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-[1.5px] border-[#1e1e1c]" style="background:#30D158"></div>
                  {:else if contact.status === "typing"}
                    <div class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-[1.5px] border-[#1e1e1c] bg-[#0A84FF] animate-pulse"></div>
                  {/if}
                </div>
                <!-- Info -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between gap-2">
                    <span class="text-[13px] font-medium text-white/85 truncate">{room.name}</span>
                    {#if room.lastTime}
                      <span class="text-[9px] text-white/25 shrink-0">{room.lastTime}</span>
                    {/if}
                  </div>
                  {#if room.lastMessage}
                    <p class="text-[11px] text-white/35 truncate mt-0.5">{room.lastMessage}</p>
                  {/if}
                </div>
                <!-- Unread badge -->
                {#if room.unread}
                  <div class="w-[18px] h-[18px] rounded-full bg-[#0A84FF] flex items-center justify-center text-[9px] font-bold text-white shrink-0">
                    {room.unread}
                  </div>
                {/if}
                <!-- Session count + chevron for agents -->
                {#if hasSessions}
                  <span class="text-[10px] font-semibold text-white/35 bg-white/[0.06] px-1.5 py-0.5 rounded shrink-0">{room.sessions?.length}</span>
                  <ChevronDown size={11} strokeWidth={2} class={`text-white/20 shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                {/if}
              </button>

              <!-- Expanded sessions (agents only) -->
              {#if isExpanded && room.sessions}
                <div class="pl-[42px] pr-2 pb-1.5 space-y-0.5">
                  {#each room.sessions as session}
                    <button class="flex items-center gap-1.5 w-full px-2 py-1 rounded-md text-left hover:bg-white/[0.05] transition-colors group">
                      <MessageSquare size={11} strokeWidth={1.5} class="text-white/25 shrink-0" />
                      <span class="text-[11px] text-white/45 truncate flex-1 group-hover:text-white/65">{session.title}</span>
                      <span class="text-[9px] text-white/20">{session.time}</span>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        {/if}

        <!-- Groups section -->
        <button class="flex items-center gap-1.5 w-full px-2 py-1.5 mt-1 text-[10px] font-semibold uppercase tracking-wider text-white/30 hover:text-white/50 transition-colors" onclick={() => toggleSection("groups")}>
          <ChevronDown size={10} strokeWidth={2} class={sectionOpen.groups ? "" : "-rotate-90"} style="transition:transform 0.15s" />
          Groups
        </button>
        {#if sectionOpen.groups}
          {#each groupRooms as room (room.id)}
            <button
              class={`flex items-center gap-2.5 w-full px-2 py-[6px] rounded-lg text-left transition-colors ${room.id === activeRoomId ? 'bg-white/[0.07]' : 'hover:bg-white/[0.04]'}`}
              onclick={() => { activeRoomId = room.id; }}
            >
              <!-- Stacked avatars -->
              <div class="flex items-center shrink-0">
                {#each room.members.slice(0, 3) as m, i}
                  <div
                    class={`w-5 h-5 ${m.kind === 'human' ? 'rounded-full' : 'rounded-md'} flex items-center justify-center text-[7px] font-bold text-white border-[1.5px] border-[#1e1e1c] relative`}
                    style="background:{m.color}; z-index:{3-i}; margin-left:{i > 0 ? '-5px' : '0'}"
                  >
                    {m.initials}
                  </div>
                {/each}
                {#if room.members.length > 3}
                  <div class="w-5 h-5 rounded-md flex items-center justify-center text-[7px] font-bold text-white/50 bg-white/10 border-[1.5px] border-[#1e1e1c] relative" style="margin-left:-5px; z-index:0">
                    +{room.members.length - 3}
                  </div>
                {/if}
              </div>
              <!-- Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-[13px] font-medium text-white/85 truncate">{room.name}</span>
                  {#if room.lastTime}
                    <span class="text-[9px] text-white/25 shrink-0">{room.lastTime}</span>
                  {/if}
                </div>
                {#if room.lastMessage}
                  <p class="text-[11px] text-white/35 truncate mt-0.5">{room.lastMessage}</p>
                {/if}
              </div>
              {#if room.unread}
                <div class="w-[18px] h-[18px] rounded-full bg-[#0A84FF] flex items-center justify-center text-[9px] font-bold text-white shrink-0">
                  {room.unread}
                </div>
              {/if}
            </button>
          {/each}
        {/if}

        <!-- Channels section -->
        <button class="flex items-center gap-1.5 w-full px-2 py-1.5 mt-1 text-[10px] font-semibold uppercase tracking-wider text-white/30 hover:text-white/50 transition-colors" onclick={() => toggleSection("channels")}>
          <ChevronDown size={10} strokeWidth={2} class={sectionOpen.channels ? "" : "-rotate-90"} style="transition:transform 0.15s" />
          Channels
        </button>
        {#if sectionOpen.channels}
          {#each channelRooms as room (room.id)}
            <button
              class={`flex items-center gap-2.5 w-full px-2 py-[6px] rounded-lg text-left transition-colors ${room.id === activeRoomId ? 'bg-white/[0.07]' : 'hover:bg-white/[0.04]'}`}
              onclick={() => { activeRoomId = room.id; }}
            >
              <div class="w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center shrink-0">
                <Hash size={14} strokeWidth={1.8} class="text-white/40" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-[13px] font-medium text-white/85 truncate">{room.name}</span>
                  {#if room.lastTime}
                    <span class="text-[9px] text-white/25 shrink-0">{room.lastTime}</span>
                  {/if}
                </div>
                {#if room.lastMessage}
                  <p class="text-[11px] text-white/35 truncate mt-0.5">{room.lastMessage}</p>
                {/if}
              </div>
            </button>
          {/each}
        {/if}
      </div>

      <!-- Sidebar settings footer -->
      <div class="sb-settings-spacer"></div>
      {#if sidebarSettingsOpen}
        <div class="sb-settings-panel">
          <div class="sb-setting-row">
            <span class="sb-setting-label">Model</span>
            <div class="sb-chips">
              <button class={chatModel === "claude" ? "sb-chip sb-chip-active" : "sb-chip"} onclick={() => chatModel = "claude"}>Claude</button>
              <button class={chatModel === "gpt4" ? "sb-chip sb-chip-active" : "sb-chip"} onclick={() => chatModel = "gpt4"}>GPT-4</button>
              <button class={chatModel === "gemini" ? "sb-chip sb-chip-active" : "sb-chip"} onclick={() => chatModel = "gemini"}>Gemini</button>
            </div>
          </div>
          <div class="sb-setting-row">
            <span class="sb-setting-label">Style</span>
            <div class="sb-chips">
              <button class={responseStyle === "fast" ? "sb-chip sb-chip-active" : "sb-chip"} onclick={() => responseStyle = "fast"}>Fast</button>
              <button class={responseStyle === "balanced" ? "sb-chip sb-chip-active" : "sb-chip"} onclick={() => responseStyle = "balanced"}>Balanced</button>
              <button class={responseStyle === "deep" ? "sb-chip sb-chip-active" : "sb-chip"} onclick={() => responseStyle = "deep"}>Deep</button>
            </div>
          </div>
          <div class="sb-setting-row">
            <span class="sb-setting-label">Memory</span>
            <button class={memoryEnabled ? "sb-toggle sb-toggle-on" : "sb-toggle"} onclick={() => memoryEnabled = !memoryEnabled}>
              <span class="sb-toggle-knob"></span>
            </button>
          </div>
          <div class="sb-setting-row">
            <span class="sb-setting-label">Streaming</span>
            <button class={streamEnabled ? "sb-toggle sb-toggle-on" : "sb-toggle"} onclick={() => streamEnabled = !streamEnabled}>
              <span class="sb-toggle-knob"></span>
            </button>
          </div>
        </div>
      {/if}
      <button class="sb-settings-trigger" class:sb-settings-active={sidebarSettingsOpen} onclick={() => sidebarSettingsOpen = !sidebarSettingsOpen}>
        <SlidersHorizontal size={13} strokeWidth={1.8} />
        <span>Settings</span>
      </button>
    </aside>

    <div class="sidebar-resize" onpointerdown={onSidebarResize}></div>

    <!-- Main chat area -->
    <main class="chat-main">
      <div class="messages-area" bind:this={messagesEl} aria-live="polite">
        <div class="messages-inner">
          {#if messages.length === 0}
            <!-- Empty state with room info -->
            <div class="empty-chat">
              {#if activeRoom.type === "channel"}
                <div class="w-12 h-12 rounded-2xl bg-white/[0.06] flex items-center justify-center mb-2">
                  <Hash size={24} strokeWidth={1.5} class="text-white/30" />
                </div>
                <p class="text-sm text-white/40 font-medium">#{activeRoom.name}</p>
                <p class="text-xs text-white/25">{activeRoom.members.length} members</p>
              {:else if activeRoom.type === "group"}
                <div class="flex items-center mb-2">
                  {#each activeRoom.members.slice(0, 4) as m, i}
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold text-white border-2 border-[#1e1e1c] relative" style="background:{m.color}; z-index:{4-i}; margin-left:{i > 0 ? '-8px' : '0'}">
                      {m.initials}
                    </div>
                  {/each}
                </div>
                <p class="text-sm text-white/40 font-medium">{activeRoom.name}</p>
                <p class="text-xs text-white/25">{activeRoom.members.length} members</p>
              {:else}
                {@const c = activeRoom.members[0]}
                <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-bold text-white mb-2" style="background:{c?.color || '#555'}">
                  {c?.initials || "?"}
                </div>
                <p class="text-sm text-white/40 font-medium">{activeRoom.name}</p>
                <p class="text-xs text-white/25">{c?.kind === "agent" ? "AI Agent" : "Human"}</p>
              {/if}
            </div>
          {:else}
            {#each messages as msg (msg.id)}
              {#if msg.role === "user"}
                <div class="msg msg-user">
                  <div class="user-bubble">{msg.content}</div>
                </div>
              {:else}
                <div class="msg msg-agent">
                  {#if msg.senderColor}
                    {@const isHumanSender = CONTACTS.find(c => c.name === msg.senderName)?.kind === "human"}
                    <div class={`w-7 h-7 ${isHumanSender ? 'rounded-full' : 'rounded-lg'} flex items-center justify-center text-[9px] font-bold text-white shrink-0 mt-0.5`} style="background:{msg.senderColor}">
                      {msg.senderName?.slice(0, 2) || "?"}
                    </div>
                  {:else}
                    <img class="chat-agent-avatar" src="/paw-avatar.png" alt="" />
                  {/if}
                  <div class="agent-bubble">
                    {#if msg.senderName && (activeRoom.type === "group" || activeRoom.type === "channel")}
                      <span class="text-[11px] font-semibold mb-1 block" style="color:{msg.senderColor || '#fff'}">{msg.senderName}</span>
                    {/if}
                    <div class="md-content">{@html renderMarkdown(msg.content)}</div>
                  </div>
                </div>
              {/if}
            {/each}

            {#if isTyping}
              <div class="msg msg-agent">
                <div class="w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-bold text-white shrink-0 mt-0.5" style="background:{activeRoom.members[0]?.color || '#555'}">
                  {activeRoom.members[0]?.initials || "?"}
                </div>
                <div class="agent-bubble typing-card">
                  <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
                </div>
              </div>
            {/if}
          {/if}
        </div>
      </div>

      <footer class="input-footer">
        <div class="input-pill liquid-glass">
          <img class="input-avatar" src="/paw-avatar.png" alt="" aria-hidden="true" />
          <input
            class="chat-input" type="text" placeholder="Type your message..."
            bind:value={inputValue} onkeydown={handleKeydown}
            disabled={isTyping} autocomplete="off" spellcheck="false"
          />
          <span class="input-action"><Mic size={16} strokeWidth={1.8} /></span>
          <span class="input-action"><Video size={16} strokeWidth={1.8} /></span>
          <span class="input-action"><Phone size={16} strokeWidth={1.8} /></span>
          <button class="send-btn" onclick={sendMessage} disabled={!inputValue.trim() || isTyping}>
            <ArrowUp size={16} strokeWidth={2} />
          </button>
        </div>
      </footer>
    </main>
  </div>
</div>

<style>
  .chat-panel {
    position: fixed;
    top: 32px; left: 0; right: 0; bottom: 0;
    z-index: 50; display: flex; flex-direction: column;
    overflow: hidden; opacity: 0; transition: opacity 200ms ease;
    border-top: 1px solid rgba(255,255,255,0.06);
    /* Override liquid-glass border/radius for full-bleed panel */
    border-radius: 0 !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
  }
  .chat-visible { opacity: 1; }

  .chat-body { display: flex; flex: 1; min-height: 0; height: 100%; overflow: hidden; }

  /* ---- Session sidebar ---- */
  .session-sidebar {
    flex-shrink: 0;
    border-right: 1px solid rgba(255,255,255,0.06);
    display: flex; flex-direction: column;
    overflow: hidden;
    min-height: 0;
    height: 100%;
  }

  .sidebar-header {
    padding: 10px 10px 6px;
    flex-shrink: 0;
  }

  .new-chat-btn {
    display: flex; align-items: center; gap: 7px;
    width: 100%; padding: 8px 12px;
    border-radius: 8px; border: none;
    background: rgba(10,132,255,0.12);
    color: #0A84FF; font-size: 13px; font-weight: 500;
    font-family: inherit; cursor: pointer;
    transition: background 0.12s;
  }
  .new-chat-btn:hover { background: rgba(10,132,255,0.20); }

  .search-row {
    display: flex; align-items: center; gap: 8px;
    margin: 4px 10px 8px; padding: 6px 10px;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.35);
  }
  .search-input {
    flex: 1; background: none; border: none; outline: none;
    font-size: 12px; font-family: inherit;
    color: rgba(255,255,255,0.80);
  }
  .search-input::placeholder { color: rgba(255,255,255,0.30); }

  .session-list {
    flex: 1; overflow-y: auto; padding: 0 6px 8px;
    display: flex; flex-direction: column; gap: 2px;
    scrollbar-width: none;
  }
  .session-list::-webkit-scrollbar { display: none; }

  /* (old session-item styles removed — now using sb-agent system) */

  /* Resize handle */
  .sidebar-resize {
    width: 5px; flex-shrink: 0; cursor: col-resize;
    position: relative; z-index: 5; margin: 0 -2px;
    transition: background 0.15s;
  }
  .sidebar-resize:hover { background: rgba(255,255,255,0.08); }

  /* ---- Main chat ---- */
  .chat-main {
    flex: 1; min-width: 0; display: flex; flex-direction: column;
  }

  .messages-area {
    flex: 1; overflow-y: auto; padding: 24px 16px;
    display: flex; justify-content: center;
    scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.10) transparent;
  }
  .messages-area::-webkit-scrollbar { width: 4px; }
  .messages-area::-webkit-scrollbar-track { background: transparent; }
  .messages-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 2px; }

  .messages-inner {
    width: 100%; max-width: 720px;
    display: flex; flex-direction: column; gap: 18px;
  }

  /* Empty state */
  .empty-chat {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 12px;
    padding-top: 20vh;
  }
  .empty-avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; opacity: 0.6; }
  .empty-text { font-size: 14px; color: rgba(255,255,255,0.35); margin: 0; }

  /* Messages — reduced glass, subtle backgrounds */
  .msg { display: flex; gap: 10px; }
  .msg-user { justify-content: flex-end; }
  .msg-agent { align-items: flex-start; }

  .chat-agent-avatar {
    width: 26px; height: 26px; border-radius: 50%;
    object-fit: cover; flex-shrink: 0; margin-top: 2px;
  }

  .user-bubble {
    max-width: 70%;
    padding: 10px 16px;
    border-radius: 18px 18px 6px 18px;
    font-size: 14px; line-height: 1.55;
    color: rgba(255,255,255,0.90);
    /* Subtle bg — no liquid-glass */
    background: rgba(10,132,255,0.12);
    border: 1px solid rgba(10,132,255,0.15);
  }

  .agent-bubble {
    flex: 1; max-width: 100%;
    padding: 14px 18px;
    border-radius: 14px;
    font-size: 14px; line-height: 1.6;
    color: rgba(255,255,255,0.85);
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
  }

  :global(.md-content .md-line) { margin: 0; }
  :global(.md-content .md-gap) { height: 8px; }
  :global(.md-content .md-numbered) { margin: 2px 0; padding-left: 8px; }
  :global(.md-content .md-bullet) { margin: 1px 0; padding-left: 24px; position: relative; }
  :global(.md-content .md-bullet::before) { content: "•"; position: absolute; left: 12px; color: rgba(255,255,255,0.50); }
  :global(.md-content strong) { font-weight: 600; color: rgba(255,255,255,0.95); }

  .typing-card {
    display: flex; align-items: center; gap: 4px;
    padding: 14px 18px; width: auto;
  }
  .typing-dot {
    display: inline-block; width: 6px; height: 6px; border-radius: 50%;
    background: rgba(255,255,255,0.40);
    animation: typing-bounce 1.2s ease-in-out infinite;
  }
  .typing-dot:nth-child(2) { animation-delay: 0.18s; }
  .typing-dot:nth-child(3) { animation-delay: 0.36s; }
  @keyframes typing-bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40% { transform: translateY(-4px); opacity: 0.85; }
  }

  /* Input footer */
  .input-footer {
    flex-shrink: 0; padding: 12px 16px 20px;
    display: flex; justify-content: center;
  }
  .input-pill {
    display: flex; align-items: center; gap: 8px;
    height: 52px; padding: 0 10px 0 8px;
    border-radius: 100px;
    width: 100%; max-width: 720px;
  }
  .input-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.50);
    flex-shrink: 0; object-fit: cover;
  }
  .chat-input {
    flex: 1; background: none; border: none; outline: none;
    height: 100%; font-size: 14px; font-family: inherit;
    color: rgba(255,255,255,0.85); caret-color: #0A84FF;
  }
  .chat-input::placeholder { color: rgba(255,255,255,0.30); }
  .chat-input:disabled { opacity: 0.5; }

  .input-action {
    display: flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%;
    color: rgba(255,255,255,0.40); cursor: pointer;
    transition: color 0.15s, background 0.15s;
  }
  .input-action:hover { color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.08); }

  .send-btn {
    width: 32px; height: 32px; border-radius: 50%; border: none;
    background: rgba(255,255,255,0.20); color: white;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; flex-shrink: 0; transition: background 0.15s, opacity 0.15s;
  }
  .send-btn:hover:not(:disabled) { background: rgba(255,255,255,0.30); }
  .send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  /* ---- Sidebar agent cards ---- */
  .sb-agent {
    margin: 1px 0; transition: background 0.12s;
  }
  .sb-agent-active { background: rgba(255,255,255,0.04); border-radius: 8px; }
  .agent-row {
    display: flex; align-items: center; gap: 8px; width: 100%;
    padding: 7px 8px; border-radius: 8px; border: none; background: none;
    cursor: pointer; transition: background 0.12s; text-align: left;
  }
  .agent-row:hover { background: rgba(255,255,255,0.05); }
  .sb-avatar {
    width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; color: #fff; letter-spacing: 0.02em;
    transition: opacity 0.15s;
  }
  .sb-info { display: flex; flex-direction: column; flex: 1; min-width: 0; gap: 1px; }
  .sb-name { font-size: 13px; font-weight: 500; color: rgba(255,255,255,0.85); }
  .sb-desc { font-size: 10px; color: rgba(255,255,255,0.32); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .sb-count {
    font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.45);
    background: rgba(255,255,255,0.06); padding: 1px 5px; border-radius: 6px;
    min-width: 16px; text-align: center;
  }
  .sb-status {
    width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
  }
  .sb-chevron {
    color: rgba(255,255,255,0.20); flex-shrink: 0;
    transition: transform 0.15s;
  }
  .sb-chevron-open { transform: rotate(180deg); }

  /* Expanded sessions under an agent */
  .sb-sessions {
    padding: 2px 4px 4px 28px; max-height: 200px; overflow-y: auto;
    scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.06) transparent;
  }
  .sb-session {
    display: flex; align-items: center; gap: 6px; width: 100%;
    padding: 4px 8px; border-radius: 6px;
    cursor: pointer; transition: background 0.12s;
    color: rgba(255,255,255,0.40);
  }
  .sb-session:hover { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.60); }
  .sb-session-active { background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.80); }
  .sb-session-title {
    font-size: 11px; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .sb-session-time { font-size: 9px; color: rgba(255,255,255,0.22); flex-shrink: 0; }
  .sb-session-del {
    opacity: 0; border: none; background: none; padding: 2px;
    color: rgba(255,255,255,0.25); cursor: pointer; transition: opacity 0.12s, color 0.12s;
    flex-shrink: 0;
  }
  .sb-session:hover .sb-session-del { opacity: 1; }
  .sb-session-del:hover { color: #FF453A; }

  /* Group chat stacked avatars */
  .grp-avatars {
    display: flex; align-items: center; flex-shrink: 0;
  }
  .grp-avatar {
    width: 20px; height: 20px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 7px; font-weight: 700; color: #fff;
    border: 1.5px solid rgba(30,30,28,0.9); position: relative;
  }
  .grp-avatar-more {
    background: rgba(255,255,255,0.12); font-size: 7px; color: rgba(255,255,255,0.55);
  }

  /* ---- Sidebar settings footer ---- */
  .sb-settings-spacer { display: none; }
  .sb-settings-trigger {
    display: flex; align-items: center; gap: 7px;
    width: 100%; padding: 8px 12px; border: none; background: none;
    color: rgba(255,255,255,0.38); font-size: 12px; font-family: inherit;
    cursor: pointer; transition: background 0.12s, color 0.12s; flex-shrink: 0;
  }
  .sb-settings-trigger:hover { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.70); }
  .sb-settings-active { color: #0A84FF !important; background: rgba(10,132,255,0.08) !important; }
  .sb-settings-panel {
    display: flex; flex-direction: column; gap: 10px;
    padding: 10px 12px; flex-shrink: 0;
    border-top: 1px solid rgba(255,255,255,0.06);
    animation: sb-in 0.12s ease-out;
  }
  @keyframes sb-in {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .sb-setting-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .sb-setting-label { font-size: 11px; color: rgba(255,255,255,0.45); flex-shrink: 0; }
  .sb-chips { display: flex; gap: 3px; flex-wrap: wrap; justify-content: flex-end; }
  .sb-chip {
    padding: 3px 7px; border-radius: 5px; border: none;
    background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.45);
    font-size: 11px; font-family: inherit; cursor: pointer;
    transition: background 0.1s, color 0.1s;
  }
  .sb-chip:hover { background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.75); }
  .sb-chip-active { background: rgba(10,132,255,0.18) !important; color: #0A84FF !important; }
  .sb-toggle {
    position: relative; width: 30px; height: 17px; border-radius: 9px;
    border: none; cursor: pointer; background: rgba(255,255,255,0.12);
    transition: background 0.15s; flex-shrink: 0; padding: 0;
  }
  .sb-toggle-on { background: rgba(10,132,255,0.55); }
  .sb-toggle-knob {
    position: absolute; top: 2px; left: 2px;
    width: 13px; height: 13px; border-radius: 50%;
    background: rgba(255,255,255,0.75); transition: left 0.15s;
  }
  .sb-toggle-on .sb-toggle-knob { left: 15px; background: white; }
</style>
