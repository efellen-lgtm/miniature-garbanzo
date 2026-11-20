
from drafter import *
from dataclasses import dataclass, field
from bakery import assert_equal
import drafter.testing
#Enables Drafter to track Bakery assertions in its testing panel.

set_website_style("retro")

@dataclass
class Yield:
    """Store the yield information for one chemical product."""
    name: str
    theoretical_yield_grams: float
    actual_yield_grams: float
    percent_yield: float


@dataclass
class State:
    """Store the information needed while the user uses the calculator."""
    reactants: list = field(default_factory=list)
    products: list = field(default_factory=list)
    yields: list = field(default_factory=list)
    calculation: str = ""
    current_index: int = 0
    current_type: str = "reactant"
    reactants_input: str = ""
    products_input: str = ""
    moles_of_part: str = ""


@dataclass
class Chemical:
    """Represent one chemical in a balanced chemical equation."""
    name: str
    coefficient: int
    moles: float
    molar_mass: float


def add_reactant(state: State, name: str, coefficient: int,
                 moles: str, molar_mass: float) -> State:
    """Add a reactant to the State's reactant list.
    An empty mole amount is stored as None because it is unknown.
    """
    if moles == "":
        moles = None
    else:
        moles = float(moles)
    state.reactants.append(
        Chemical(name, coefficient, moles, molar_mass)
    )
    return state


def add_product(state: State, name: str, coefficient: int,
                moles: str, molar_mass: float) -> State:
    """Add a product to the State's product list.
    An empty mole amount is stored as None because it is unknown.
    """
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
    """Display a textbox for entering a chemical's mole amount."""
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


def calculate_lower_amount(
    reactants: list[Chemical]
) -> Chemical | None:
    """Find the limiting reactant using mole amounts and coefficients.
    Returns the reactant with the smallest mole-to-coefficient ratio.
    Returns None if no reactants have known amounts.
    """
    known_reactants = []
    for reactant in reactants:
        if reactant.moles is not None:
            known_reactants.append(reactant)
    if len(known_reactants) == 0:
        return None
    minimum_reactant = known_reactants[0]
    for reactant in known_reactants:
        if (reactant.moles / reactant.coefficient <
                minimum_reactant.moles /
                minimum_reactant.coefficient):
            minimum_reactant = reactant
    return minimum_reactant


def calculate_missing_moles(state: State) -> bool:
    """Calculate unknown mole amounts using a known chemical amount.
    This function is intended for the mole-ratio calculation.
    Returns False if no known mole amounts were entered.
    """
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
                limiting_reactant = calculate_lower_amount(
                    state.reactants
                )
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
    """Display the calculated mole amounts for all chemicals."""
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
    """Choose and perform the calculation selected by the user."""
    if state.calculation in [
        "theoretical_yield",
        "percent_yield",
        "limiting_reactant"
    ]:
        for reactant in state.reactants:
            if reactant.moles is None:
                return Page(state, [
                    "Please enter the actual mole amount for every reactant.",
                    Button("Go Back", "input_part")
                ])
    if state.calculation == "moles":
        success = calculate_missing_moles(state)
        if not success:
            return Page(state, [
                "You must enter at least one known mole amount.",
                Button("Go Back", "input_part")
            ])
        return display_moles(state)
    elif state.calculation == "theoretical_yield":
        state.current_index = 0
        return input_molar_mass(state)
    elif state.calculation == "percent_yield":
        state.current_index = 0
        return input_molar_mass(state)
    elif state.calculation == "limiting_reactant":
        return calculate_limiting_reactant(state)
    return Page(state, ["Calculation type not recognized."])


def find_theoretical_yield(
    product: Chemical,
    limiting_reactant: Chemical
) -> float:
    """Calculate theoretical product moles from the limiting reactant."""
    product_moles = (
        limiting_reactant.moles *
        product.coefficient /
        limiting_reactant.coefficient
    )
    return product_moles


@route
def input_molar_mass(state: State) -> Page:
    """Ask the user to enter a product's molar mass."""
    product = state.products[state.current_index]
    return Page(state, [
        "Enter the molar mass of " + product.name,
        "Enter the value in grams per mole (g/mol).",
        TextBox("molar_mass_input"),
        Button("Submit", "save_molar_mass")
    ])


@route
def save_molar_mass(
    state: State,
    molar_mass_input: str
) -> Page:
    """Save a product's molar mass and move to the next product."""
    molar_mass = float(molar_mass_input)
    if molar_mass <= 0:
        return Page(state, [
            "Molar mass must be greater than zero.",
            Button("Go Back", "input_molar_mass")
        ])
    product = state.products[state.current_index]
    product.molar_mass = molar_mass
    state.current_index += 1
    if state.current_index < len(state.products):
        return input_molar_mass(state)
    return calculate_theoretical_yield(state)


@route
def calculate_theoretical_yield(state: State) -> Page:
    """Calculate the theoretical yield in grams for each product."""
    limiting_reactant = calculate_lower_amount(state.reactants)
    # Check whether a limiting reactant was found.
    if limiting_reactant is None:
        return Page(state, [
            "Enter the mole amounts for your reactants first."
        ])
    # Check whether the limiting reactant has a positive amount.
    if limiting_reactant.moles <= 0:
        return Page(state, [
            "The limiting reactant must have more than zero moles."
        ])
    state.yields = []
    results = ["Theoretical Product Yields:"]
    for product in state.products:
        theoretical_moles = find_theoretical_yield(
            product, limiting_reactant
        )
        theoretical_grams = theoretical_moles * product.molar_mass
        state.yields.append(
            Yield(product.name, theoretical_grams, 0.0, 0.0)
        )
        results.append(
            product.name + ": " +
            str(theoretical_grams) + " grams"
        )
    if state.calculation == "percent_yield":
        state.current_index = 0
        return input_actual_yield(state)
    return Page(state, results)


@route
def input_actual_yield(state: State) -> Page:
    """Ask the user to enter the actual yield for a product."""
    product = state.products[state.current_index]
    return Page(state, [
        "Enter the actual yield for " + product.name,
        "Enter the amount in grams.",
        TextBox("actual_yield_input"),
        Button("Submit", "save_actual_yield")
    ])


@route
def save_actual_yield(
    state: State,
    actual_yield_input: str
) -> Page:
    """Save an actual yield and move to the next product."""
    actual_yield = float(actual_yield_input)
    if actual_yield < 0:
        return Page(state, [
            "Actual yield cannot be negative.",
            Button("Go Back", "input_actual_yield")
        ])
    product_yield = state.yields[state.current_index]
    product_yield.actual_yield_grams = actual_yield
    state.current_index += 1
    if state.current_index < len(state.products):
        return input_actual_yield(state)
    return calculate_percent_yield(state)


@route
def calculate_percent_yield(state: State) -> Page:
    """Calculate and display the percent yield for every product."""
    results = ["Percent Yields:"]
    for product_yield in state.yields:
        if product_yield.theoretical_yield_grams <= 0:
            return Page(state, [
                "Cannot calculate percent yield because "
                + product_yield.name
                + " has a theoretical yield of zero."
            ])
        product_yield.percent_yield = (
            product_yield.actual_yield_grams /
            product_yield.theoretical_yield_grams
        ) * 100
        results.append(
            product_yield.name + ": " +
            str(round(product_yield.percent_yield, 2)) + "%"
        )
    return Page(state, results)


@route
def calculate_limiting_reactant(state: State) -> Page:
    """Find and display the limiting reactant."""
    limiting_reactant = calculate_lower_amount(state.reactants)
    if limiting_reactant is None:
        return Page(state, [
            "Enter the mole amounts for your reactants first."
        ])
    return Page(
        state,
        "Limiting Reactant: " + limiting_reactant.name
    )


@route
def save_moles(state: State, moles_of_part: str) -> Page:
    """Save a mole amount and move to the next chemical."""
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
    if state.current_type == "reactant":
        if state.current_index < len(state.reactants):
            return input_part(state)
        state.current_type = "product"
        state.current_index = 0
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
    """Display textboxes for entering reactants and products."""
    return Page(state, [
        "Write reactants with coefficients separated by commas.",
        "Example: 1 CH4, 2 O2",
        TextBox("reactants_input"),
        "Write products with coefficients separated by commas.",
        "Example: 1 CO2, 2 H2O",
        TextBox("products_input"),
        Button("Submit", "process_equation")
    ])


@route
def process_equation(
    state: State,
    reactants_input: str,
    products_input: str
) -> Page:
    """Read the equation text and create Chemical instances."""
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
    """Start a mole calculation."""
    state.yields = []
    state.current_index = 0
    state.current_type = "reactant"
    state.calculation = "moles"
    return calculate_equation(state)


@route
def limiting_reactant_problem(state: State) -> Page:
    """Start a limiting-reactant calculation."""
    state.yields = []
    state.current_index = 0
    state.current_type = "reactant"
    state.calculation = "limiting_reactant"
    return calculate_equation(state)


@route
def theoretical_yield_problem(state: State) -> Page:
    """Start a theoretical-yield calculation."""
    state.yields = []
    state.current_index = 0
    state.current_type = "reactant"
    state.calculation = "theoretical_yield"
    return calculate_equation(state)


@route
def percent_yield_problem(state: State) -> Page:
    """Start a percent-yield calculation."""
    state.yields = []
    state.current_index = 0
    state.current_type = "reactant"
    state.calculation = "percent_yield"
    return calculate_equation(state)


@route
def index(state: State) -> Page:
    """Display the homepage and the four calculation choices."""
    return Page(state, [
        Header("Process Chemical Equations"),
        "What do you want to calculate?",
        Button("Moles of a Substance", "moles_problem"),
        Button("Limiting Reactant", "limiting_reactant_problem"),
        Button("Theoretical Yield", "theoretical_yield_problem"),
        Button("Percent Yield", "percent_yield_problem")
    ])


test_reactants = [
    Chemical("CH4", 1, 3.0, None),
    Chemical("O2", 2, 4.0, None)
]
assert_equal(
    calculate_lower_amount(test_reactants).name,
    "O2"
)
unknown_reactants = [
    Chemical("CH4", 1, None, None),
    Chemical("O2", 2, None, None)
]
assert_equal(
    calculate_lower_amount(unknown_reactants),
    None
)
test_limiting_reactant = Chemical("CH4", 1, 2.0, None)
test_product = Chemical("CO2", 1, None, 44.01)
assert_equal(
    find_theoretical_yield(test_product, test_limiting_reactant),
    2.0
)
test_water = Chemical("H2O", 2, None, 18.02)
assert_equal(
    find_theoretical_yield(test_water, test_limiting_reactant),
    4.0
)
test_state = State(
    reactants=[
        Chemical("CH4", 1, 2.0, None),
        Chemical("O2", 2, None, None)
    ],
    products=[
        Chemical("CO2", 1, None, None),
        Chemical("H2O", 2, None, None)
    ]
)
assert_equal(calculate_missing_moles(test_state), True)
assert_equal(test_state.reactants[1].moles, 4.0)
assert_equal(test_state.products[0].moles, 2.0)
assert_equal(test_state.products[1].moles, 4.0)

test_yield_state = State(
    yields=[
        Yield("CO2", 88.02, 70.0, 0.0)
    ]
)
calculate_percent_yield(test_yield_state)
assert_equal(
    test_yield_state.yields[0].percent_yield,
    79.53
)
test_theoretical_state = State(
    reactants=[
        Chemical("CH4", 1, 2.0, None),
        Chemical("O2", 2, 4.0, None)
    ],
    products=[
        Chemical("CO2", 1, None, 44.01)
    ],
    calculation="theoretical_yield"
)
calculate_theoretical_yield(test_theoretical_state)
assert_equal(
    test_theoretical_state.yields[0].theoretical_yield_grams,
    88.02
)


start_server(State())
