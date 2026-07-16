from umwelt.host.api import GameHost
from septacrypt_core.scenario.manifold_ship import build_ship_manifold
from septacrypt_core.scenario.campaign import CampaignManager
from septacrypt_core.repl.bot import RandomBot, GreedyTensionBot
import time

def run_simulation(bot_class, iterations: int = 1000, max_turns: int = 200):
    wins = 0
    total_turns = 0
    attention_spent = 0.0
    timeouts = 0

    print(f"--- Booting Monte Carlo Simulation: {bot_class.__name__} ({iterations} runs) ---")
    start_time = time.time()

    for i in range(iterations):
        host = GameHost()  # bare/unregistered -- never touches host.engine; only .turn is read
        zone_clusters = build_ship_manifold()
        campaign = CampaignManager(host, zone_clusters)
        bot = bot_class(f"bot_{i}")

        turn_count = 0
        won = False

        while turn_count < max_turns and campaign.attention_budget > 0:
            turn_count += 1
            result = bot.play_turn(campaign)
            if result == "VICTORY" or campaign.check_victory():
                wins += 1
                won = True
                break

        if not won:
            timeouts += 1

        total_turns += turn_count
        attention_spent += (50.0 - campaign.attention_budget)

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
    print(f"  -> Compute Time: {elapsed:.2f}s\n")

    return {
        "bot": bot_class.__name__,
        "iterations": iterations,
        "win_rate": win_rate,
        "timeout_rate": timeout_rate,
        "avg_turns": avg_turns,
        "avg_attention": avg_att,
        "elapsed_s": elapsed,
    }

def run_churn(n=2500):
    print("=========================================================================")
    print("       FLEDGELING SEPTACRYPT: MONTE CARLO PLAYTESTING INITIATED          ")
    print("=========================================================================\n")

    results = []
    results.append(run_simulation(RandomBot, iterations=n))
    results.append(run_simulation(GreedyTensionBot, iterations=n))

    print("=========================================================================")
    print("  [COMPLETE] STATISTICAL CHURN FINISHED. READY FOR COUPLING TUNING.      ")
    print("=========================================================================")
    return results

if __name__ == "__main__":
    run_churn()
