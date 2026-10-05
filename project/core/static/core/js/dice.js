export function setupDiceRoller() {
    const form = document.getElementById("diceForm");
    if (!form) return;

    const button = form.querySelector("button[type=submit]");
    const result = document.getElementById("diceResult");
    const error = document.getElementById("diceError");
    const log = document.getElementById("log");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        button.disabled = true;
        result.textContent = "";
        error.textContent = "";

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
            });

            if (!response.ok) {
                if (response.status === 400) {
                    const errors = await response.json();
                    error.textContent = Object.values(errors).flat().join(" ");
                } else {
                    error.textContent = "Couldn't roll the dice. Try again or reload the page.";
                }
                return;
            }

            const roll = await response.json();
            const message = `${roll.count}d${roll.sides}: ${roll.rolls.join(" + ")} = ${roll.total}`;
            result.textContent = message;

            const entry = document.createElement("p");
            entry.className = "small mb-2";
            entry.textContent = message;
            log.prepend(entry);
        } catch (err) {
            error.textContent = "Couldn't reach the server. Check your connection and try again.";
        } finally {
            button.disabled = false;
        }
    });
}
