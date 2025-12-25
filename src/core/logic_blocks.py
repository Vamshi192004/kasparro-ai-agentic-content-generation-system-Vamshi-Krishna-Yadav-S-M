"""
Logic Blocks - Shared Reusable Logic
"""

class LogicBlocks:
    @staticmethod
    def format_currency(amount, currency):
        return f"{amount:,.2f} {currency}"

    @staticmethod
    def generate_seo_title(product_name, category):
        return f"{product_name} | Best {category} Review & Specs"

    @staticmethod
    def generate_disclaimer():
        return "Disclaimer: Product specifications and prices are subject to change. Please verify with the manufacturer."

    @staticmethod
    def format_list(items):
        return "\n".join([f"- {item}" for item in items])

    # --- Specific Blocks for Requirements ---

    @staticmethod
    def generate_benefits_block(features):
        """
        Transforms features into benefits.
        Example: "Vitamin C" -> "Brightens skin" (Simulated logic)
        """
        benefits = []
        for feature in features:
            if "Vitamin C" in feature:
                benefits.append("Brightens and evens skin tone")
            elif "Hyaluronic" in feature:
                benefits.append("Deeply hydrates and plumps")
            elif "SPF" in feature:
                benefits.append("Protects against UV damage")
            else:
                benefits.append(f"Provides the benefit of {feature}")
        return benefits

    @staticmethod
    def extract_usage_block(product_data):
        """
        Extracts usage instructions based on product type/specs.
        """
        app_method = product_data.get("specs", {}).get("application", "Apply as needed")
        return f"Usage Instructions: {app_method}. For best results, use daily."

    @staticmethod
    def compare_ingredients_block(product_features, competitor_ingredients):
        """
        Compares main product features (proxy for ingredients) vs competitor ingredients.
        """
        main_ingredients = ", ".join(product_features[:3]) # Simulating main ingredients from top features
        comp_ingredients = ", ".join(competitor_ingredients)
        return f"{main_ingredients} VS {comp_ingredients}"
