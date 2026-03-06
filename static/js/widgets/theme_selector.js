class ThemeSelector extends HTMLElement {
  constructor() {
    super();
    this.lsKey = "ml-theme";
  }

  connectedCallback() {
    const savedTheme = localStorage.getItem(this.lsKey) || "NONE";

    this.label = document.createElement("label");
    this.label.textContent = "Theme: ";

    this.select = document.createElement("select");

    const themes = {
      NONE: "Browser default",
      dark: "Dark",
      "dark-purple": "Dark Purple",
      rarity: "Rarity",
      "princess-luna": "Princess Luna",
    };

    for (const [value, text] of Object.entries(themes)) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      if (value === savedTheme) option.selected = true;
      this.select.appendChild(option);
    }

    this.select.addEventListener("change", () => this.updateTheme());

    this.innerHTML = "";
    this.appendChild(this.label);
    this.appendChild(this.select);
  }

  updateTheme() {
    const oldTheme = localStorage.getItem(this.lsKey);
    const newTheme = this.select.value;

    // Удаляем старый класс, если он был
    if (oldTheme && oldTheme !== "NONE") {
      document.documentElement.classList.remove(oldTheme);
    }

    if (newTheme === "NONE") {
      localStorage.removeItem(this.lsKey);
    } else {
      document.documentElement.classList.add(newTheme);
      localStorage.setItem(this.lsKey, newTheme);
    }

    console.info(`Theme changed to: ${newTheme}`);
  }
}

if (!customElements.get("theme-selector")) {
  customElements.define("theme-selector", ThemeSelector);
}
