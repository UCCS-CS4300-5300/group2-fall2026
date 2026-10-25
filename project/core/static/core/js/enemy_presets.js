export function setupPreset() {
    const enemySearchForm = document.getElementById("enemyForm");
    const input = document.getElementById("enemyInput");
    const status = document.getElementById("enemyStatus");
    const results = document.getElementById("enemyResults");

    // Do nothing if Enemy Preset HTML is not preset
    if (!enemySearchForm || !input || !status || !results) {
        return;
    }

    enemySearchForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const query = input.value.trim();

        if(!query) {
            status.textContent = "Please enter a monster name. ";
            results.replaceChildren();
            return;
        }

        status.textContent = "Searching for monster...";
        results.replaceChildren();


        try {
            // Asking Django to search for the monster
            const response = await fetch(
                `/api/enemies/?q=${encodeURIComponent(query)}`,
                {
                    headers: {
                        "Accept": "application/json",
                    },
                }
            );

            const data = await response.json();

            if(!response.ok) {
                throw new Error(
                    data.error || "Monster search failed."
                );
            }

            const monsters = data.monsters;

            if(!Array.isArray(monsters) || monsters.length == 0) {
                status.textContent = "No matching monsters found.";
                return;
            }

            status.textContent = `Found ${monsters.length} monster(s)`;

            monsters.forEach((monster) => {
                // Create a card to display the return stats
                const card = document.createElement("div");
                card.className = "card mb-3";

                const body = document.createElement("div");
                body.className = "card-body";

                const heading = document.createElement("h3");
                heading.className = "h5 card-title";
                heading.textContent = monster.name || "Unknown monster";
                body.appendChild(heading);

                if (monster.image) {
                    const image = document.createElement("img");
                    image.src = monster.image;
                    image.alt = monster.name || "Monster image";
                    image.className = "img-fluid rounded mb-3";
                    image.style.maxHeight = "180px";
                    image.style.objectFit = "contain";
                    image.loading = "lazy";

                    body.appendChild(image);
                }

                const details = [
                    ["Size", monster.size],
                    ["Type", monster.type],
                    ["Alignment", monster.alignment],
                    ["Armor Class", monster.armor_class],
                    ["Hit Points", monster.hit_points],
                    ["Speed", monster.speed],
                    ["Challenge Rating", monster.challenge_rating],
                    ["XP", monster.xp],
                    ["STR", monster.strength],
                    ["DEX", monster.dexterity],
                    ["CON", monster.constitution],
                    ["INT", monster.intelligence],
                    ["WIS", monster.widom],
                    ["CHA", monster.charisma],
                ];

                details.forEach(([label, value]) => {
                    if(value === null || value === undefined) {
                        return;
                    }

                    const paragraph = document.createElement("p");
                    paragraph.className = "small mb-1";

                    const strong = document.createElement("strong");
                    strong.textContent = `${label}: `;

                    const displayValue = 
                        typeof value === "object"
                            ? JSON.stringify(value)
                            : String(value);

                    paragraph.appendChild(strong);
                    paragraph.appendChild(
                        document.createTextNode(displayValue)
                    );

                    body.appendChild(paragraph);
                });

                if (
                    Array.isArray(monster.actions) &&
                    monster.actions.length > 0
                )  {
                    const actionsHeading = document.createElement("h4");
                    actionsHeading.className = "h6 mt-3";
                    actionsHeading.textContent = "Actions";

                    body.appendChild(actionsHeading);

                    monster.actions.forEach((action) => {
                        const paragraph = document.createElement("p");
                        paragraph.className = "small mb-2";

                        const name = document.createElement("strong");
                        name.textContent = `${action.name || "Action"}: `;

                        paragraph.appendChild(name);
                        paragraph.appendChild(document.createTextNode(
                            action.desc || "No description available."
                        ));

                        body.appendChild(paragraph);
                    });
                }

                card.appendChild(body);
                results.appendChild(card);
            });
        } catch (error) {
            console.error("Enemy preset search error:", error);
            status.textContent = `Error: ${error.message}`;
        }
    });
}