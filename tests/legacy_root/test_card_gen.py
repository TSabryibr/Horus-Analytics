from core.ReportGenerator import create_horus_signal_card
import io

buf = create_horus_signal_card(
    ticker="SWDY",
    entry=18.7500,
    stop_loss=17.5000,
    tp1=21.0000,
    score=8,
    rsi=58.1,
    volume_x=1.8,
    tp2=23.0,
    signal_data_date="04 Mar",
    signal_label="PRE-CLOSE SIGNAL"
)

with open("test_card.png", "wb") as f:
    f.write(buf.getvalue())

print("Generated test_card.png")
