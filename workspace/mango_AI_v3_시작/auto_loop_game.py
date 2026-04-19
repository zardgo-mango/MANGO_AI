import random
import tkinter as tk


class AutoLoopGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Auto Loop Arena")
        self.root.geometry("760x560")
        self.root.minsize(700, 520)
        self.root.configure(bg="#101722")

        self.tick_ms = 250
        self.running = True

        self.day = 1
        self.wave = 1
        self.gold = 0
        self.kills = 0
        self.auto_attack = 4
        self.crit_rate = 0.12
        self.armor = 0
        self.potion_count = 1
        self.hero_max_hp = 100
        self.hero_hp = self.hero_max_hp
        self.hero_regen = 1

        self.enemy_name = ""
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.enemy_attack = 0
        self._spawn_enemy()

        self.status_var = tk.StringVar()
        self.hero_var = tk.StringVar()
        self.enemy_var = tk.StringVar()
        self.log_var = tk.StringVar()

        self._build_ui()
        self._refresh_ui("The battle loop is running.")
        self._schedule_loop()

    def _build_ui(self) -> None:
        title = tk.Label(
            self.root,
            text="AUTO LOOP ARENA",
            font=("Consolas", 24, "bold"),
            bg="#101722",
            fg="#f3f6fb",
            pady=14,
        )
        title.pack()

        top_frame = tk.Frame(self.root, bg="#101722", padx=18, pady=6)
        top_frame.pack(fill="x")

        self.status_label = tk.Label(
            top_frame,
            textvariable=self.status_var,
            justify="left",
            anchor="w",
            font=("Consolas", 11),
            bg="#182334",
            fg="#d8e1ee",
            padx=14,
            pady=12,
        )
        self.status_label.pack(fill="x")

        center = tk.Frame(self.root, bg="#101722", padx=18, pady=12)
        center.pack(fill="both", expand=True)
        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=1)

        hero_panel = tk.LabelFrame(
            center,
            text="Hero",
            font=("Consolas", 12, "bold"),
            bg="#182334",
            fg="#f3f6fb",
            bd=0,
            padx=14,
            pady=14,
        )
        hero_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        enemy_panel = tk.LabelFrame(
            center,
            text="Enemy",
            font=("Consolas", 12, "bold"),
            bg="#182334",
            fg="#f3f6fb",
            bd=0,
            padx=14,
            pady=14,
        )
        enemy_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        hero_label = tk.Label(
            hero_panel,
            textvariable=self.hero_var,
            justify="left",
            anchor="nw",
            font=("Consolas", 12),
            bg="#182334",
            fg="#d8e1ee",
        )
        hero_label.pack(fill="both", expand=True)

        enemy_label = tk.Label(
            enemy_panel,
            textvariable=self.enemy_var,
            justify="left",
            anchor="nw",
            font=("Consolas", 12),
            bg="#182334",
            fg="#d8e1ee",
        )
        enemy_label.pack(fill="both", expand=True)

        controls = tk.Frame(self.root, bg="#101722", padx=18, pady=10)
        controls.pack(fill="x")

        buttons = [
            ("Attack Up (12G)", self.buy_attack),
            ("Regen Up (15G)", self.buy_regen),
            ("Armor Up (18G)", self.buy_armor),
            ("Buy Potion (10G)", self.buy_potion),
            ("Pause / Resume", self.toggle_running),
            ("Reset", self.reset_game),
        ]

        for text, command in buttons:
            button = tk.Button(
                controls,
                text=text,
                command=command,
                font=("Segoe UI", 10, "bold"),
                bg="#f4b860",
                fg="#1c2430",
                activebackground="#ffd087",
                activeforeground="#1c2430",
                bd=0,
                relief="flat",
                padx=10,
                pady=8,
                cursor="hand2",
            )
            button.pack(side="left", padx=4)

        log_frame = tk.Frame(self.root, bg="#101722", padx=18, pady=(4, 18))
        log_frame.pack(fill="x")

        log_title = tk.Label(
            log_frame,
            text="Recent Event",
            font=("Consolas", 12, "bold"),
            bg="#101722",
            fg="#f3f6fb",
            anchor="w",
        )
        log_title.pack(fill="x", pady=(0, 4))

        log_label = tk.Label(
            log_frame,
            textvariable=self.log_var,
            font=("Consolas", 11),
            justify="left",
            anchor="w",
            bg="#182334",
            fg="#9cd67b",
            padx=14,
            pady=12,
        )
        log_label.pack(fill="x")

    def _schedule_loop(self) -> None:
        self.root.after(self.tick_ms, self._game_loop)

    def _game_loop(self) -> None:
        if self.running:
            self._simulate_tick()
        self._schedule_loop()

    def _simulate_tick(self) -> None:
        self.day += 1
        event = self._hero_attack()

        if self.enemy_hp > 0:
            event = self._enemy_attack(event)

        self.hero_hp = min(self.hero_max_hp, self.hero_hp + self.hero_regen)

        if self.hero_hp <= 0:
            event = self._use_potion_or_revive()

        self._refresh_ui(event)

    def _hero_attack(self) -> str:
        damage = self.auto_attack + random.randint(0, 4)
        prefix = "Critical hit" if random.random() < self.crit_rate else "Attack"
        if prefix == "Critical hit":
            damage *= 2

        self.enemy_hp = max(0, self.enemy_hp - damage)
        event = f"{prefix}! {self.enemy_name} takes {damage} damage."

        if self.enemy_hp == 0:
            reward = 6 + self.wave * 2
            self.gold += reward
            self.kills += 1
            event = f"{self.enemy_name} defeated. Reward: {reward} gold."
            self.wave += 1
            self._spawn_enemy()

        return event

    def _enemy_attack(self, current_event: str) -> str:
        incoming = max(1, self.enemy_attack - self.armor)
        self.hero_hp = max(0, self.hero_hp - incoming)
        return f"{current_event} Counterattack deals {incoming} damage."

    def _use_potion_or_revive(self) -> str:
        if self.potion_count > 0:
            self.potion_count -= 1
            self.hero_hp = self.hero_max_hp // 2
            return "The hero fell, but a potion restored half HP."

        penalty = min(self.gold, 12)
        self.gold -= penalty
        self.hero_hp = self.hero_max_hp
        self.wave = max(1, self.wave - 1)
        self._spawn_enemy()
        return f"Defeat. Lost {penalty} gold and dropped back to wave {self.wave}."

    def _spawn_enemy(self) -> None:
        names = ["Slime", "Goblin", "Skeleton", "Beast", "Shade", "War Machine"]
        self.enemy_name = random.choice(names)
        self.enemy_max_hp = 20 + self.wave * 9
        self.enemy_hp = self.enemy_max_hp
        self.enemy_attack = 3 + self.wave * 2

    def _refresh_ui(self, event_text: str) -> None:
        mode = "RUN" if self.running else "PAUSE"
        self.status_var.set(
            f"Mode: {mode}    Day: {self.day}    Wave: {self.wave}    Gold: {self.gold}    Kills: {self.kills}"
        )
        self.hero_var.set(
            "\n".join(
                [
                    f"HP: {self.hero_hp} / {self.hero_max_hp}",
                    f"Auto attack: {self.auto_attack}",
                    f"Crit rate: {int(self.crit_rate * 100)}%",
                    f"Armor: {self.armor}",
                    f"Regen per tick: {self.hero_regen}",
                    f"Potions: {self.potion_count}",
                ]
            )
        )
        self.enemy_var.set(
            "\n".join(
                [
                    f"Name: {self.enemy_name}",
                    f"HP: {self.enemy_hp} / {self.enemy_max_hp}",
                    f"Attack: {self.enemy_attack}",
                    "Each loop tick resolves one hero action and one enemy action.",
                ]
            )
        )
        self.log_var.set(event_text)

    def _spend_gold(self, amount: int) -> bool:
        if self.gold < amount:
            self._refresh_ui(f"Not enough gold. Need {amount} gold.")
            return False
        self.gold -= amount
        return True

    def buy_attack(self) -> None:
        if not self._spend_gold(12):
            return
        self.auto_attack += 2
        self.crit_rate = min(0.5, self.crit_rate + 0.02)
        self._refresh_ui("Attack power increased. Crit rate also improved.")

    def buy_regen(self) -> None:
        if not self._spend_gold(15):
            return
        self.hero_regen += 1
        self.hero_max_hp += 10
        self.hero_hp = min(self.hero_max_hp, self.hero_hp + 12)
        self._refresh_ui("Regen increased and max HP expanded.")

    def buy_armor(self) -> None:
        if not self._spend_gold(18):
            return
        self.armor += 1
        self._refresh_ui("Armor increased.")

    def buy_potion(self) -> None:
        if not self._spend_gold(10):
            return
        self.potion_count += 1
        self._refresh_ui("Bought one potion.")

    def toggle_running(self) -> None:
        self.running = not self.running
        state_text = "Auto loop resumed." if self.running else "Auto loop paused."
        self._refresh_ui(state_text)

    def reset_game(self) -> None:
        self.day = 1
        self.wave = 1
        self.gold = 0
        self.kills = 0
        self.auto_attack = 4
        self.crit_rate = 0.12
        self.armor = 0
        self.potion_count = 1
        self.hero_max_hp = 100
        self.hero_hp = self.hero_max_hp
        self.hero_regen = 1
        self.running = True
        self._spawn_enemy()
        self._refresh_ui("Game state reset.")


def main() -> None:
    root = tk.Tk()
    AutoLoopGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
