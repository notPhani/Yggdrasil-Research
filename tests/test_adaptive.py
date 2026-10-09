from ygg.narratives.adaptive import AdaptiveConfig, AdaptiveEmergence

def test_diurnal_scaling_adjusts_threshold():
    cfg = AdaptiveConfig(m_min=3, rho=0.004)
    ad = AdaptiveEmergence(cfg)
    
    # Simulate low volume night (800 roots/window)
    for _ in range(24):
        ad.record_window(800)
    assert ad.current_m_rate() == 4
    
    # Simulate high volume day (6000 roots/window)
    for _ in range(24):
        ad.record_window(6000)
    assert ad.current_m_rate() == 24

def test_velocity_surge_fires_on_rapid_arrivals():
    ad = AdaptiveEmergence(AdaptiveConfig(m_min=3, v_burst_base=2.5))
    for _ in range(24):
        ad.record_window(5000)  # m_rate is 20
        
    cid = 101
    # 4 articles in 30 minutes (0.5 hours) -> velocity = 8.0 docs/h
    assert ad.should_emerge(cid, mass=4, t_h=1.0, num_alive=50) is True

def test_slow_drip_does_not_surge():
    ad = AdaptiveEmergence(AdaptiveConfig(m_min=3, v_burst_base=2.5))
    for _ in range(24):
        ad.record_window(5000)  # m_rate is 20
        
    cid = 202
    # Register arrival at t_h = 1.0
    ad.should_emerge(cid, mass=1, t_h=1.0, num_alive=50)
    # 4 articles across 5 hours -> velocity = 0.8 docs/h < 2.5
    assert ad.should_emerge(cid, mass=4, t_h=6.0, num_alive=50) is False

def test_capacity_cap_enforces_stricter_barrier():
    ad = AdaptiveEmergence(AdaptiveConfig(m_min=3, max_alive=100))
    for _ in range(24):
        ad.record_window(1000)  # m_rate is 4
        
    # At capacity (100 alive), requires 2 * m_rate = 8
    assert ad.should_emerge(303, mass=5, t_h=1.0, num_alive=100) is False
    assert ad.should_emerge(303, mass=8, t_h=1.0, num_alive=100) is True
