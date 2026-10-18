// Attacks and initiative can use this without changing the log or character stats.
export function rollDice(sides, count) {
    if (![4, 6, 8, 10, 12, 20].includes(sides)) {
        throw new Error("Choose a d4, d6, d8, d10, d12, or d20.");
    }
    if (!Number.isInteger(count) || count < 1 || count > 20) {
        throw new Error("Enter a whole number of dice from 1 to 20.");
    }

    const rolls = [];
    for (let i = 0; i < count; i++) {
        rolls.push(Math.floor(Math.random() * sides) + 1);
    }
    const total = rolls.reduce((sum, roll) => sum + roll, 0);
    return { sides, count, rolls, total };
}

export function setupDiceRoller() {
    const form = document.getElementById("diceForm");
    if (!form) return;

    const button = form.querySelector("button[type=submit]");
    const result = document.getElementById("diceResult");
    const error = document.getElementById("diceError");
    const log = document.getElementById("log");

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        result.textContent = "";
        error.textContent = "";

        try {
            const sides = Number(form.elements.namedItem("sides").value);
            const count = Number(form.elements.namedItem("count").value);
            const roll = rollDice(sides, count);
            const message = `${roll.count}d${roll.sides}: ${roll.rolls.join(" + ")} = ${roll.total}`;
            result.textContent = message;

            const entry = document.createElement("p");
            entry.className = "small mb-2";
            entry.textContent = message;
            log.prepend(entry);
        } catch (err) {
            error.textContent = err.message;
        }
    });
    button.disabled = false;
}
