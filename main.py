from drafter import *
from dataclasses import dataclass, field

@dataclass
class State:
    reactants: list = field(default_factory=list)
    products: list = field(default_factory=list)
    #field(default_factory=list) creates a new empty list whenever a State is created
    calculation: str = ""
    current_index: int = 0
    current_type: str = "reactant"
    reactants_input: str = ""
    products_input: str = ""
    moles_of_part: str = ""

@dataclass
class Chemical:
    name: str
    coefficient: int
    moles: float
    molar_mass: float
    
def add_reactant(state: State, name, coefficient, moles, molar_mass):
    if moles == "":
        moles = None
    else:
        moles = float(moles)

    state.reactants.append(
        Chemical(name, coefficient, moles, molar_mass)
    )

    return state

def add_product(state, name, coefficient, moles, molar_mass):
    if moles == "":
        moles = None
    else:
        moles = float(moles)

    state.products.append(
        Chemical(name, coefficient, moles, molar_mass)
    )

    return state


@route
def input_part(state: State) -> Page:

    if state.current_type == "reactant":
        chemical = state.reactants[state.current_index]
    else:
        chemical = state.products[state.current_index]

    return Page(state, [
        "Input the moles for " + chemical.name,
        "If unknown, input 0.",
        TextBox("moles_of_part"),
        Button("Submit", "save_moles")
    ])

def calculate_lower_amount(reactants: list[Chemical]) -> Chemical:
    known_reactants = []
    for reactant in reactants:
        if reactant.moles is not None:
            known_reactants.append(reactant)
    
    if len(known_reactants) == 0:
        return None
    
    minimum_reactant = known_reactants[0]
    for reactant in known_reactants:
        if reactant.moles/reactant.coefficient < minimum_reactant.moles/minimum_reactant.coefficient:
            minimum_reactant = reactant
    return minimum_reactant

def calculate_missing_moles(state):
    known = None
    known_reactants = 0
    known_products = 0

    for chemical in state.reactants:
        if chemical.moles is not None:
            known_reactants += 1
            if known is None:
                known = chemical
    
    for chemical in state.products:
        if chemical.moles is not None:
            known_products += 1
            if known is None:
                known = chemical

    if known_reactants + known_products == 0:
        return False

    for chemical in state.reactants + state.products:
        if chemical.moles is None:
            if known_reactants > 1:
                limiting_reactant = calculate_lower_amount(state.reactants)
                chemical.moles = (
                    limiting_reactant.moles *
                    chemical.coefficient /
                    limiting_reactant.coefficient
                )
            else:
                chemical.moles = (
                    known.moles *
                    chemical.coefficient /
                    known.coefficient
                )
    return True

@route
def display_moles(state: State) -> Page:

    results = ["Calculated Mole Amounts:"]

    for chemical in state.reactants:
        results.append(
            chemical.name + ": " +
            str(chemical.moles) + " moles"
        )

    for chemical in state.products:
        results.append(
            chemical.name + ": " +
            str(chemical.moles) + " moles"
        )

    return Page(state, results)

@route
def calculate_moles(state: State) -> Page:
    success = calculate_missing_moles(state)

    if not success:
        return Page(state, [
            "You must enter at least one known mole amount.",
            Button("Go Back", "input_part")
        ])

    if state.calculation == "moles":
        return display_moles(state)

    elif state.calculation == "theoretical_yield":
        return calculate_theoretical_yield(state)

    elif state.calculation == "percent_yield":
        return calculate_percent_yield(state)

    elif state.calculation == "limiting_reactant":
        return calculate_limiting_reactant(state)

    return Page(state, ["Calculation type not recognized."])

@route
def calculate_limiting_reactant(state: State) -> Page:
    limiting_reactant = calculate_lower_amount(state.reactants)
    return Page(state, "Limiting_Reactant: " + limiting_reactant.name)

@route
def save_moles(state: State, moles_of_part: str) -> Page:
    moles = float(moles_of_part)

    if state.current_type == "reactant":
        chemical = state.reactants[state.current_index]
    else:
        chemical = state.products[state.current_index]

    if moles == 0:
        chemical.moles = None
    else:
        chemical.moles = moles

    state.current_index += 1

    # Check if there are more reactants
    if state.current_type == "reactant":
        if state.current_index < len(state.reactants):
            return input_part(state)

        # Move on to products
        state.current_type = "product"
        state.current_index = 0

    # Check if there are more products
    else:
        if state.current_index < len(state.products):
            return input_part(state)

        return Page(state, [
            "All chemical information has been entered!",
            Button("Calculate", "calculate_moles")
        ])

    return input_part(state)

@route
def calculate_equation(state: State) -> Page:
    return Page(state, [
        "Write reactants with coefficients separated by commas. Include coefficient for each.",
        "Example: 1 CH4, 2 O2",
        TextBox("reactants_input"),

        "Write products with coefficients separated by commas. Include coefficient for each.",
        "Example: 1 CO2, 2 H2O",
        TextBox("products_input"),

        Button("Submit", "process_equation")
    ])

@route
def process_equation(state: State, reactants_input: str, products_input: str) -> Page:
    state.reactants = []
    state.products = []

    reactant_list = reactants_input.split(",")
    product_list = products_input.split(",")

    for item in reactant_list:
        parts = item.strip().split()

        if len(parts) != 2:
            return Page(state, [
                "Invalid reactant format: " + item,
                "Please use coefficient followed by formula.",
                "Example: 1 CH4, 2 O2",
                Button("Go Back", "calculate_equation")
            ])

        coefficient = int(parts[0])
        name = parts[1]

        add_reactant(state, name, coefficient, "", None)

    for item in product_list:
        parts = item.strip().split()

        if len(parts) != 2:
            return Page(state, [
                "Invalid product format: " + item,
                "Please use coefficient followed by formula.",
                "Example: 1 CO2, 2 H2O",
                Button("Go Back", "calculate_equation")
            ])

        coefficient = int(parts[0])
        name = parts[1]

        add_product(state, name, coefficient, "", None)

    state.current_index = 0
    state.current_type = "reactant"

    return input_part(state)

@route
def moles_problem(state: State) -> Page:
    state.calculation = "moles"
    return calculate_equation(state)

@route
def limiting_reactant_problem(state: State) -> Page:
    state.calculation = "limiting_reactant"
    return calculate_equation(state)

@route
def theoretical_yield_problem(state: State) -> Page:
    state.calculation = "theoretical_yield"
    return calculate_equation(state)

@route
def percent_yield_problem(state: State) -> Page:
    state.calculation = "percent_yield"
    return calculate_equation(state)
    

@route
def index(state: State) -> Page:
    return Page(state, [
        "What do you want to calculate?",
        Button("Moles of a Substance", "moles_problem"),
        Button("Limiting Reactant", "limiting_reactant_problem"),
        Button("Theoretical Yield", "theoretical_yield_problem"),
        Button("Percent Yield", "percent_yield_problem")
    ])


start_server(State())
