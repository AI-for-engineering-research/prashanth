# Hand-rolled property-based tests using Julia's built-in Test stdlib.
# No external PBT package required. The pattern: generate random inputs in a loop,
# assert a property or metamorphic relation, report failure via @test.
#
# Domain: ideal Brayton (gas-turbine) cycle efficiency + Celsius ↔ Kelvin conversion.
#
# Copy this file and adapt:
#   1. Replace the domain functions with your own.
#   2. Replace rand_r() / rand_γ() with generators for your domain.
#   3. Replace each @testset body with properties that must hold for your code.
#
# Run with:
#   julia property_test_julia.jl
#
# For full PBT (automatic shrinking, strategy composition):
#   - Supposition.jl (active, Hypothesis-inspired): https://github.com/Seelengrab/Supposition.jl
#   - PropCheck.jl (maintenance mode): https://github.com/Seelengrab/PropCheck.jl

using Test

# ── Domain functions ───────────────────────────────────────────────────────────

"""Thermal efficiency of an ideal Brayton cycle.
   r = pressure ratio (>1), γ = ratio of specific heats (>1)"""
brayton_efficiency(r, γ) = 1.0 - r^(-(γ - 1) / γ)

"""Isentropic temperature ratio across a compressor: T2/T1 = r^((γ-1)/γ)"""
isentropic_temp_ratio(r, γ) = r^((γ - 1) / γ)

"""Celsius to Kelvin."""
celsius_to_kelvin(C) = C + 273.15

"""Kelvin to Celsius."""
kelvin_to_celsius(K) = K - 273.15

# ── Random input generators ────────────────────────────────────────────────────
# ADAPT: change the lo / hi bounds to match your domain's physically valid range.
rand_r(lo=1.1, hi=40.0)  = lo + rand() * (hi - lo)   # pressure ratio (must be > 1)
rand_γ(lo=1.1, hi=1.7)   = lo + rand() * (hi - lo)   # ratio of specific heats (must be > 1)
rand_celsius(lo=-200.0, hi=2000.0) = lo + rand() * (hi - lo)

N = 1000  # trials per property; raise to 5000 for a thorough run

# ── Properties ────────────────────────────────────────────────────────────────

@testset "Brayton Cycle Properties" begin

    @testset "Efficiency is strictly between 0 and 1 (absolute invariant)" begin
        # Physical requirement: thermal efficiency must be in (0, 1) for any r > 1, γ > 1.
        # If this fails, the formula has a sign error or the exponent is wrong.
        for _ in 1:N
            r, γ = rand_r(), rand_γ()
            η = brayton_efficiency(r, γ)
            if !(0 < η < 1)
                @error "Efficiency out of (0,1)" r γ η expected="0 < η < 1"
            end
            @test 0 < η < 1
        end
    end

    @testset "Efficiency increases with pressure ratio (monotonicity MR)" begin
        # Metamorphic relation: higher r → higher η at fixed γ.
        # Generate r1 first, then r2 > r1, and check the ordering of outputs.
        for _ in 1:N
            r1 = rand_r(1.1, 20.0)
            r2 = rand_r(r1 + 0.1, 40.0)   # r2 strictly greater than r1
            γ  = rand_γ()
            η1 = brayton_efficiency(r1, γ)
            η2 = brayton_efficiency(r2, γ)
            if !(η2 > η1)
                @error "Monotonicity MR violated: higher r must give higher η" r1 r2 γ η1 η2 expected="η(r2) > η(r1)"
            end
            @test η2 > η1
        end
    end

    @testset "Efficiency → 0 as pressure ratio → 1 (limit property)" begin
        # As r → 1⁺ the cycle collapses and η → 0.
        # This catches off-by-one errors in the exponent sign.
        for _ in 1:N
            r = 1.0 + rand() * 0.01   # r in (1.0, 1.01), very close to 1
            γ = rand_γ()
            η = brayton_efficiency(r, γ)
            if !(η < 0.02)
                @error "Limit property violated: η must be < 0.02 when r ≈ 1" r γ η expected="η < 0.02"
            end
            @test η < 0.02
        end
    end

    @testset "Isentropic ratio is inverse of expansion ratio (round-trip MR)" begin
        # Metamorphic relation (inverse): compress by r, then expand by r → back to start.
        # isentropic_ratio(r, γ) * isentropic_ratio(1/r, γ) == 1.0
        for _ in 1:N
            r, γ = rand_r(), rand_γ()
            fwd = isentropic_temp_ratio(r, γ)
            bwd = isentropic_temp_ratio(1/r, γ)
            product = fwd * bwd
            if !isapprox(product, 1.0; rtol=1e-10)
                @error "Round-trip MR violated: ratio(r,γ)*ratio(1/r,γ) must equal 1" r γ fwd bwd product expected=1.0
            end
            @test isapprox(product, 1.0; rtol=1e-10)
        end
    end

end

@testset "Celsius ↔ Kelvin Conversion Properties" begin

    @testset "Round-trip C → K → C (inverse MR)" begin
        # Metamorphic relation (round-trip): converting to Kelvin and back must recover C.
        for _ in 1:N
            C = rand_celsius()
            K = celsius_to_kelvin(C)
            C2 = kelvin_to_celsius(K)
            if !isapprox(C2, C; atol=1e-10)
                @error "Round-trip C→K→C failed" C K C2 expected=C atol=1e-10
            end
            @test isapprox(C2, C; atol=1e-10)
        end
    end

    @testset "Round-trip K → C → K (inverse MR, other direction)" begin
        for _ in 1:N
            K = rand() * 2273.15   # 0 to 2273.15 K
            C = kelvin_to_celsius(K)
            K2 = celsius_to_kelvin(C)
            if !isapprox(K2, K; atol=1e-10)
                @error "Round-trip K→C→K failed" K C K2 expected=K atol=1e-10
            end
            @test isapprox(K2, K; atol=1e-10)
        end
    end

    @testset "Order-preserving: warmer Celsius → warmer Kelvin (monotonicity MR)" begin
        # Metamorphic relation: the ordering of temperatures must be preserved across units.
        for _ in 1:N
            C1 = rand_celsius()
            C2 = rand_celsius()
            C1 == C2 && continue   # skip exact ties (degenerate case)
            K1 = celsius_to_kelvin(C1)
            K2 = celsius_to_kelvin(C2)
            if !((C1 < C2) == (K1 < K2))
                @error "Monotonicity MR violated: ordering must be preserved" C1 C2 K1 K2 expected="(C1<C2)==(K1<K2)"
            end
            @test (C1 < C2) == (K1 < K2)
        end
    end

    @testset "Kelvin is always 273.15 more than Celsius (absolute offset)" begin
        # Absolute invariant: the offset must be exactly 273.15 for every input.
        for _ in 1:N
            C = rand_celsius()
            offset = celsius_to_kelvin(C) - C
            if !isapprox(offset, 273.15; atol=1e-10)
                @error "Offset property violated: K - C must equal 273.15" C offset expected=273.15 atol=1e-10
            end
            @test isapprox(offset, 273.15; atol=1e-10)
        end
    end

end
