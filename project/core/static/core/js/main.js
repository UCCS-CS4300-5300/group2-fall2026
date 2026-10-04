/* ---------- State ---------- */
let combatants = []; // {id,name,type,maxHp,hp,ac,init,atk,dmg,x,y,initRoll}
let selectedId = null; // attacker
let attacking = false; // waiting for a target click
let turnIdx = -1;
let nextId = 1;

const $ = (id) => document.getElementById(id); //Shorhand to get element from ID
const board = $("board"); //First element with "board" id

/* ---------- Dice ---------- */

//Roll Dice function
const d = (sides) => Math.floor(Math.random() * sides) + 1;

//TODO: This function is AI slop. We should rewrite this to be more readable.
function rollDamage(expr, crit) {
    //Regex for damage calculations. i.e. 1d6+6
    const m = expr.match(/^(\d+)d(\d+)([+-]\d+)?$/);

    //No Regex for damage roll. Default to 1
    if (!m) {
        return { total: 1, text: "1" };
    }

    //Damage amount. Double for crit.
    let n = +m[1] * (crit ? 2 : 1),
        rolls = [];

    //Roll each die and add to rolls list
    for (let i = 0; i < n; i++) {
        rolls.push(d(+m[2]));
    }

    //Todal damage done.
    const mod = +(m[3] || 0);
    const total = Math.max(0, rolls.reduce((a, b) => a + b, 0) + mod);

    //Returns {total damage, text representation}
    return {
        total,
        text: `[${rolls.join("+")}]${mod ? (mod > 0 ? "+" : "") + mod : ""}`,
    };
}

/* ---------- Log ---------- */

//Add something to the log.
function log(html, cls = "") {
    const el = document.createElement("div");
    el.className = "log-entry " + cls;
    el.innerHTML = html;
    $("log").prepend(el);
}

//HTML escape stuff. No XSS on my freaking watch.
const esc = (s) =>
    s.replace(
        /[&<>"]/g,
        (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
    );

/* ---------- Rendering ---------- */

//TODO: Also slop.
function render() {
    //Take all combatants and remove from DOM.
    board.querySelectorAll(".combatant").forEach((e) => e.remove());

    //"emptyMsg" element not shown if there's combatants
    $("emptyMsg").style.display = combatants.length ? "none" : "";

    const turnId = combatants[turnIdx]?.id;

    combatants.forEach((c) => {
        const el = document.createElement("div");
        el.className =
            `combatant ${c.type}` +
            (c.id === selectedId ? " selected" : "") +
            (c.hp <= 0 ? " dead" : "") +
            (attacking && c.id !== selectedId && c.hp > 0 ? " targetable" : "");
        el.dataset.id = c.id;
        el.style.left = c.x + "px";
        el.style.top = c.y + "px";
        const pct = Math.max(0, (c.hp / c.maxHp) * 100);
        el.innerHTML = `
      ${c.initRoll != null ? `<div class="init-badge" title="Initiative">${c.initRoll}</div>` : ""}
      <h5 class="name mb-1">${esc(c.name)}${c.id === turnId ? " &#9876;" : ""}</h5>
      <div class="small text-secondary mb-2">${c.type === "player" ? "Player" : "Enemy"} &middot; AC ${c.ac}</div>
      <div class="hp-track mb-1"><div class="hp-fill" style="width:${pct}%;${c.type === "enemy" ? "background:var(--blood)" : ""}"></div></div>
      <div class="small">HP ${Math.max(0, c.hp)} / ${c.maxHp}</div>
      <div class="small text-secondary">Hits +${c.atk} for ${esc(c.dmg)}</div>`;
        board.appendChild(el);
    });
    $("attackBtn").disabled = selectedId == null || attacking;
    $("nextBtn").disabled = turnIdx < 0;
    $("hint").textContent = attacking
        ? "Click a target."
        : selectedId
          ? "Attacker selected. Press Attack."
          : "";
    const cur = combatants[turnIdx];
    $("turnInfo").textContent = cur
        ? `Turn: ${cur.name}`
        : "Roll initiative to begin";
}

/* ---------- Drag + click on cards ---------- */
let drag = null;

//Lets you drag cards with "combatant" class
board.addEventListener("pointerdown", (e) => {
    const el = e.target.closest(".combatant");
    if (!el) return;
    const c = combatants.find((x) => x.id == el.dataset.id);
    drag = {
        c,
        el,
        sx: e.clientX,
        sy: e.clientY,
        ox: c.x,
        oy: c.y,
        moved: false,
    };
    el.setPointerCapture(e.pointerId);
});

board.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.sx,
        dy = e.clientY - drag.sy;
    if (!drag.moved && Math.hypot(dx, dy) < 5) return;
    drag.moved = true;
    drag.el.classList.add("dragging");
    drag.c.x = Math.max(0, drag.ox + dx);
    drag.c.y = Math.max(0, drag.oy + dy);
    drag.el.style.left = drag.c.x + "px";
    drag.el.style.top = drag.c.y + "px";
});

board.addEventListener("pointerup", () => {
    if (!drag) return;
    const { c, moved } = drag;
    drag = null;
    if (!moved) handleCardClick(c);
    else render();
});

function handleCardClick(c) {
    if (attacking) {
        if (c.id === selectedId || c.hp <= 0) return;
        doAttack(
            combatants.find((x) => x.id === selectedId),
            c,
        );
        attacking = false;
    } else {
        selectedId = selectedId === c.id ? null : c.id;
    }
    render();
}

/* ---------- Combat ---------- */
function doAttack(a, t) {
    const roll = d(20),
        total = roll + a.atk;
    const nat20 = roll === 20,
        nat1 = roll === 1;
    const hit = nat20 || (!nat1 && total >= t.ac);
    const head = `<b>${esc(a.name)}</b> attacks <b>${esc(t.name)}</b>: d20 <span class="roll">${roll}</span> + ${a.atk} = <span class="roll">${total}</span> vs AC ${t.ac}`;
    if (!hit) {
        log(`${head}. ${nat1 ? "Critical miss!" : "Miss."}`, "miss");
        return;
    }
    const dmg = rollDamage(a.dmg, nat20);
    t.hp -= dmg.total;
    log(
        `${head}. ${nat20 ? "Critical hit! " : "Hit! "}${dmg.text} = <span class="roll">${dmg.total}</span> damage.` +
            (t.hp <= 0 ? ` <b>${esc(t.name)} is down.</b>` : ""),
        "hit",
    );
}

$("attackBtn").onclick = () => {
    attacking = true;
    render();
};

$("initBtn").onclick = () => {
    if (!combatants.length) return;
    combatants.forEach((c) => (c.initRoll = d(20) + c.init));
    combatants.sort((a, b) => b.initRoll - a.initRoll);
    turnIdx = 0;
    log(
        "<b>Initiative:</b> " +
            combatants.map((c) => `${esc(c.name)} ${c.initRoll}`).join(", "),
    );
    render();
};

$("nextBtn").onclick = () => {
    if (!combatants.length) return;
    for (let i = 0; i < combatants.length; i++) {
        turnIdx = (turnIdx + 1) % combatants.length;
        if (combatants[turnIdx].hp > 0) break;
    }
    selectedId = combatants[turnIdx].id;
    attacking = false;
    render();
};

$("resetBtn").onclick = () => {
    if (!confirm("Remove all combatants and clear the log?")) return;
    combatants = [];
    selectedId = null;
    attacking = false;
    turnIdx = -1;
    $("log").innerHTML = "";
    render();
};

/* ---------- Add combatant ---------- */

$("addForm").onsubmit = (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    const n = combatants.length;
    combatants.push({
        id: nextId++,
        name: f.name.trim(),
        type: f.type,
        maxHp: +f.hp,
        hp: +f.hp,
        ac: +f.ac,
        init: +f.init,
        atk: +f.atk,
        dmg: f.dmg || "1d6",
        x: 20 + (n % 3) * 230,
        y: 20 + Math.floor(n / 3) * 190,
        initRoll: null,
    });
    log(`${esc(f.name)} joined the encounter.`);
    e.target.reset();
    bootstrap.Modal.getInstance($("addModal")).hide();
    render();
};

/* ---------- Quests ---------- */
$("questForm").onsubmit = (e) => {
    e.preventDefault();
    const li = document.createElement("li");
    li.className = "list-group-item d-flex gap-2 align-items-start";
    li.innerHTML = `<input class="form-check-input mt-1" type="checkbox"><span class="flex-grow-1">${esc($("questInput").value)}</span>
    <button class="btn-close btn-sm" aria-label="Remove"></button>`;
    li.querySelector("input").onchange = (ev) =>
        li
            .querySelector("span")
            .classList.toggle(
                "text-decoration-line-through",
                ev.target.checked,
            );
    li.querySelector("button").onclick = () => li.remove();
    $("quests").appendChild(li);
    $("questInput").value = "";
};

/* ---------- Demo data so it isn't empty on first load ---------- */
[
    ["Aria", "player", 24, 15, 2, 5, "1d8+3"],
    ["Goblin", "enemy", 7, 13, 2, 4, "1d6+2"],
    ["Goblin Boss", "enemy", 21, 15, 1, 4, "1d8+2"],
].forEach(([name, type, hp, ac, init, atk, dmg], n) =>
    combatants.push({
        id: nextId++,
        name,
        type,
        maxHp: hp,
        hp,
        ac,
        init,
        atk,
        dmg,
        x: 20 + n * 230,
        y: 20,
        initRoll: null,
    }),
);

render();
