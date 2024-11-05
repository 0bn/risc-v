from myhdl import block, always_comb, Signal, intbv, delay, instance, Simulation, StopSimulation, traceSignals

@block
def RadiationAlertSystem(radiation_level, limit, alert, alert_mode, exposure_time, accumulated_radiation, event_radiation_log, event_alert_log, protection_mode):
    """
    sistema de alerta de radiação
    - radiation_level: entrada com o nível atual de radiação cósmica
    - limit: o limite de radiação segura
    - alert: saída que aciona o alerta (0 = seguro, 1 = alerta ativo)
    - alert_mode: nível de alerta (0 = seguro, 1 = alerta moderado, 2 = alerta crítico)
    - exposure_time: quanto tempo o sistema já ficou exposto a radiação acima do limite seguro
    - accumulated_radiation: acumula o total de radiação ao longo do tempo
    - event_radiation_log: log básico para registrar níveis de radiação críticos
    - event_alert_log: log para registrar níveis de alerta
    - protection_mode: modo de proteção para reduzir riscos (simula um "modo seguro")
    """
    max_exposure_time = 3  # tempo máximo de exposição antes de dar alerta
    critical_limit = limit + 50  # nível de radiação que já consideramos crítico
    log_index = Signal(intbv(0, min=0, max=len(event_radiation_log)))  # índice de eventos no log

    @always_comb
    def check_radiation():
        # evitar estouro ao acumular radiação
        new_accumulated = accumulated_radiation + radiation_level
        if new_accumulated < accumulated_radiation.max:
            accumulated_radiation.next = new_accumulated
        else:
            accumulated_radiation.next = accumulated_radiation.max - 1  # definir como o máximo menos 1 para evitar estouro

        if radiation_level > critical_limit:
            alert_mode.next = 2
            protection_mode.next = 1
        elif radiation_level > limit:
            alert_mode.next = 1
        else:
            alert_mode.next = 0
            protection_mode.next = 0

        if alert_mode != 0:
            exposure_time.next = exposure_time + 1
        else:
            exposure_time.next = 0

        if exposure_time >= max_exposure_time or accumulated_radiation >= 300:
            alert.next = 1
            event_radiation_log[int(log_index)].next = int(radiation_level)
            event_alert_log[int(log_index)].next = int(alert_mode)
            log_index.next = (log_index + 1) % len(event_radiation_log)
        else:
            alert.next = 0

    return check_radiation

@block
def test_radiation_alert():
    radiation_level = Signal(intbv(0)[8:])
    limit = Signal(intbv(100)[8:])
    alert = Signal(intbv(0)[1:])
    alert_mode = Signal(intbv(0)[2:])
    exposure_time = Signal(intbv(0)[4:])
    accumulated_radiation = Signal(intbv(0)[16:])
    protection_mode = Signal(intbv(0)[1:])

    event_radiation_log = [Signal(intbv(0)[8:]) for _ in range(10)]
    event_alert_log = [Signal(intbv(0)[2:]) for _ in range(10)]

    alert_system = RadiationAlertSystem(
        radiation_level, limit, alert, alert_mode, 
        exposure_time, accumulated_radiation, 
        event_radiation_log, event_alert_log, 
        protection_mode
    )
    
    radiation_levels = [45, 75, 150, 90, 200, 50, 110, 160, 40, 180]

    @instance
    def stimulus():
        print("iniciando teste do sistema de alerta de radiação...\n")
        count = 0
        max_cycles = 30  # limite o número de ciclos
        while count < max_cycles:
            radiation_level.next = radiation_levels[count % len(radiation_levels)]
            yield delay(10)

            alert_status = "ativo" if int(alert) else "inativo"
            mode_desc = ["seguro", "moderado", "crítico"][int(alert_mode)]
            protection_status = "ativado" if int(protection_mode) else "desativado"
            print(f"nível de radiação: {int(radiation_level)}, alerta: {alert_status}, modo: {mode_desc}, proteção: {protection_status}")
            count += 1

            # condição para parar a simulação se um alerta for ativado
            if int(alert):
                print("alerta ativado! parando a simulação.")
                break

        raise StopSimulation

    return alert_system, stimulus

# simulação com rastreamento de sinais para o gtkwave
test_inst = test_radiation_alert()
trace_inst = traceSignals(test_inst)
sim = Simulation(trace_inst)
sim.run()
