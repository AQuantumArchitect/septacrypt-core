"""Monte Carlo playtesting, layered entirely on top of GameSession's public
API -- never touching World/WorldStepper/CertifiedTransaction directly. The
hardened transaction layer is a black box here; this harness only calls
wait/look/status/quest_status/victory/stir.
"""
from septacrypt_core.api.session import GameSession
from septacrypt_core.repl.bot import RandomBot, GreedyTensionBot, TargetBitBot, TensionRelieverBot
import time

def run_simulation(bot_class, iterations: int = 1000, max_turns: int = 200, base_seed: int = 0):
    wins = 0
    total_turns = 0
    attention_spent = 0.0
    timeouts = 0
    action_counts = {"WAIT": 0, "LOOK": 0, "STIR": 0}

    print(f"--- Booting Monte Carlo Simulation: {bot_class.__name__} ({iterations} runs) ---")
    start_time = time.time()

    for i in range(iterations):
        seed = base_seed + i
        game = GameSession(
            mode="ship",
            seed=seed,
            enable_ledger=False,       # certified stamping isn't the thing under test here
            private_observers=False,   # ground-truth beliefs for these bots (not player-fog testing)
            attention_budget=50.0,
        )
        bot = bot_class(f"bot_{i}", seed=seed)

        turn_count = 0
        won = False

        while turn_count < max_turns and (game.attention_budget is None or game.attention_budget > 0):
            turn_count += 1
            action = bot.play_turn(game)
            action_counts[action] = action_counts.get(action, 0) + 1
            if action == "VICTORY" or game.victory():
                wins += 1
                won = True
                break

        if not won:
            timeouts += 1

        total_turns += turn_count
        attention_spent += (50.0 - (game.attention_budget or 0.0))

    elapsed = time.time() - start_time
    win_rate = (wins / iterations) * 100
    timeout_rate = (timeouts / iterations) * 100
    avg_turns = total_turns / iterations
    avg_att = attention_spent / iterations

    print(f"[RESULTS] {bot_class.__name__}:")
    print(f"  -> Win Rate: {win_rate:.2f}%")
    print(f"  -> Deadlock/Timeout Rate: {timeout_rate:.2f}%")
    print(f"  -> Avg Turns to Finish/Fail: {avg_turns:.1f}")
    print(f"  -> Avg Attention Spent: {avg_att:.1f}")
    print(f"  -> Action mix: {action_counts}")
    print(f"  -> Compute Time: {elapsed:.2f}s\n")

    return {
        "bot": bot_class.__name__,
        "iterations": iterations,
        "win_rate": win_rate,
        "timeout_rate": timeout_rate,
        "avg_turns": avg_turns,
        "avg_attention": avg_att,
        "action_counts": action_counts,
        "elapsed_s": elapsed,
    }

def run_churn(n=2500):
    print("=========================================================================")
    print("       FLEDGELING SEPTACRYPT: MONTE CARLO PLAYTESTING INITIATED          ")
    print("=========================================================================\n")

    results = []
    results.append(run_simulation(RandomBot, iterations=n))
    results.append(run_simulation(GreedyTensionBot, iterations=n))
    results.append(run_simulation(TargetBitBot, iterations=n))
    results.append(run_simulation(TensionRelieverBot, iterations=n))

    print("=========================================================================")
    print("  [COMPLETE] STATISTICAL CHURN FINISHED. READY FOR COUPLING TUNING.      ")
    print("=========================================================================")
    return results

if __name__ == "__main__":
    run_churn()
