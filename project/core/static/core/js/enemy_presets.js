function formatSpeed(speed) {
    // if monster has no speed return null
    if (!speed) {
        return null;
    }

    // If speed is already a string return it
    if (typeof speed === "string") {
        return speed;
    } 

    // Convert other non-object values to strings
    if (typeof speed !== "object") {
        return String(speed);
    }

    // Replace each speed entry into readable label and value
    const parts = Object.entries(speed)
        .filter(([key, value]) =>
            key !== "hover" &&
            value !== null &&
            value !== undefined &&
            value !== false
    )
    .map(([key, value]) => {
        // Replace underscores and capitalize movement type
        const label = key
            .replace(/_/g, " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());

        // Display boolean movement properities as labels
        if (typeof value === "boolean") {
            return label;
        }

        // Combine movement type and its speed
        return `${label}: ${value}`;
    });

    // Join all movement speeds into a readable string
    return parts.length > 0 ? parts.join(", ") : "Not specified"
}

/*
Set up monster presets earch form
Called from main.js
*/
export function setupPreset() {
    // Find the form and elements used to show search results
    const enemySearchForm = document.getElementById("enemyForm");
    const input = document.getElementById("enemyInput");
    const status = document.getElementById("enemyStatus");
    const results = document.getElementById("enemyResults");

    // Do nothing if Enemy Preset HTML is not preset
    if (!enemySearchForm || !input || !status || !results) {
        return;
    }

    // Run when user submits a monster search
    enemySearchForm.addEventListener("submit", async (event) => {
        // Prevents the form from reloading
        event.preventDefault();

        // Get monster name + remover whitespace
        const query = input.value.trim();

        // Dont search if input is empty
        if(!query) {
            status.textContent = "Please enter a monster name. ";
            results.replaceChildren();
            return;
        }

        // Telling user the search is in progess
        status.textContent = "Searching for monster...";
        results.replaceChildren();


        try {
            // Asking Django to search for the monster
            const response = await fetch(
                `/api/enemies/?q=${encodeURIComponent(query)}`,
                {
                    headers: {
                        "Accept": "application/json", // Request JSON from Django
                    },
                }
            );

            // Convert response body from JSON to JS
            const data = await response.json();

            // Error thrown if server returns unsuccessful status
            if(!response.ok) {
                throw new Error(
                    data.error || "Monster search failed."
                );
            }

            // Django returns results in "monsters array"
            const monsters = data.monsters;

            // Handling missing/empty search results
            if(!Array.isArray(monsters) || monsters.length == 0) {
                status.textContent = "No matching monsters found.";
                return;
            }

            // Telling user how many monsters were found
            status.textContent = `Found ${monsters.length} monster(s)`;

            // Creating a separate card for every monster
            monsters.forEach((monster) => {
                // Create a card to display the return stats
                const card = document.createElement("div");
                card.className = "card mb-3";

                // Creating container for cards contents
                const body = document.createElement("div");
                body.className = "card-body";

                // Display monsters name as card heading
                const heading = document.createElement("h3");
                heading.className = "h5 card-title";
                heading.textContent = monster.name || "Unknown monster";
                body.appendChild(heading);

                // Display monster image
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

                // Prepare monsters basic stats for display
                const details = [
                    ["Size", monster.size],
                    ["Type", monster.type],
                    ["Alignment", monster.alignment],
                    ["Armor Class",
                         monster.armor_class == null
                            ? null
                            : `${monster.armor_class}${
                                monster.armor_class_type
                                    ? ` (${monster.armor_class_type})`
                                    : ""
                            }`,
                    ],
                    ["Hit Points", monster.hit_points],
                    ["Speed", formatSpeed(monster.speed)],
                    ["Challenge Rating", monster.challenge_rating],
                    ["XP", monster.xp],
                    ["STR", monster.strength],
                    ["DEX", monster.dexterity],
                    ["CON", monster.constitution],
                    ["INT", monster.intelligence],
                    ["WIS", monster.widom],
                    ["CHA", monster.charisma],
                ];

                // Creating paragraph for available stats
                details.forEach(([label, value]) => {
                    if(value === null || value === undefined) {
                        return;
                    }

                    const paragraph = document.createElement("p");
                    paragraph.className = "small mb-1";

                    // Making stats label bold
                    const strong = document.createElement("strong");
                    strong.textContent = `${label}: `;

                    // COnverting objects & nums into displayable text
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

                // Displaying monster actions if they are available
                if (
                    Array.isArray(monster.actions) &&
                    monster.actions.length > 0
                )  {
                    const actionsHeading = document.createElement("h4");
                    actionsHeading.className = "h6 mt-3";
                    actionsHeading.textContent = "Actions";

                    body.appendChild(actionsHeading);

                    // Displaying each actions name and description
                    monster.actions.forEach((action) => {
                        const paragraph = document.createElement("p");
                        paragraph.className = "small mb-2";

                        const name = document.createElement("strong");

                        // Fallback if action has no name
                        name.textContent = `${action.name || "Action"}: `;

                        paragraph.appendChild(name);
                        // Display action description if available
                        paragraph.appendChild(document.createTextNode(
                            action.desc || "No description available."
                        ));

                        body.appendChild(paragraph);
                    });
                }

                // Place contents inside the card
                card.appendChild(body);
                results.appendChild(card);
            });
        } catch (error) {
            console.error("Enemy preset search error:", error);
            status.textContent = `Error: ${error.message}`;
        }
    });
}