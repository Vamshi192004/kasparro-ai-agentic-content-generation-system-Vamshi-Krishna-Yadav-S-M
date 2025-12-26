"""
Integration tests for the agentic content generation system.
These tests use REAL LLM API calls to verify end-to-end functionality.

WARNING: These tests will consume API credits. Use sparingly.
"""
import pytest
import os
import json
from dotenv import load_dotenv
from core.graph import create_graph
from core.state import AgentState
from core.schemas import ProductSchema, FAQPageSchema, ProductPageSchema, ComparisonPageSchema

# Load environment variables
load_dotenv()

# Skip tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping integration tests"
)


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "GlowBoost Vitamin C Serum",
        "category": "Skincare",
        "price": 49.99,
        "currency": "USD",
        "description": "A powerful vitamin C serum that brightens skin, reduces dark spots, and provides antioxidant protection for a radiant, youthful complexion.",
        "features": [
            "20% Pure Vitamin C (L-Ascorbic Acid)",
            "Hyaluronic Acid for deep hydration",
            "Ferulic Acid for enhanced stability",
            "Lightweight, fast-absorbing formula",
            "Suitable for all skin types"
        ],
        "specs": {
            "volume": "30ml",
            "pH": "3.5",
            "shelf_life": "12 months after opening"
        },
        "competitors": [
            {
                "name": "SkinCeuticals C E Ferulic",
                "price": 166.00
            },
            {
                "name": "The Ordinary Vitamin C Suspension 23%",
                "price": 5.80
            }
        ]
    }


@pytest.fixture
def app():
    """Create the LangGraph application."""
    return create_graph()


class TestEndToEndPipeline:
    """Test the complete pipeline with real LLM calls."""
    
    @pytest.mark.slow
    def test_full_pipeline_execution(self, app, sample_product_data):
        """Test complete pipeline execution from raw data to final outputs."""
        # Initialize state
        initial_state = {
            "raw_data": sample_product_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        # Execute pipeline
        final_state = app.invoke(initial_state)
        
        # Verify all outputs were generated
        assert final_state.get('clean_data') is not None, "Parser failed to generate clean_data"
        assert final_state.get('questions') is not None, "Question generator failed"
        assert final_state.get('faq_page') is not None, "FAQ page generation failed"
        assert final_state.get('product_page') is not None, "Product page generation failed"
        assert final_state.get('comparison_page') is not None, "Comparison page generation failed"
        
        # Verify data types
        assert isinstance(final_state['clean_data'], ProductSchema)
        assert isinstance(final_state['faq_page'], FAQPageSchema)
        assert isinstance(final_state['product_page'], ProductPageSchema)
        assert isinstance(final_state['comparison_page'], ComparisonPageSchema)
        
        print(f"\n✓ Pipeline completed successfully")
        print(f"  - Revision count: {final_state.get('revision_count', 0)}")
        print(f"  - FAQ count: {len(final_state['faq_page'].faqs)}")
        print(f"  - Questions generated: {len(final_state['questions'])}")
    
    @pytest.mark.slow
    def test_faq_count_validation(self, app, sample_product_data):
        """Test that FAQ page has at least 15 questions."""
        initial_state = {
            "raw_data": sample_product_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        final_state = app.invoke(initial_state)
        
        # CRITICAL: Verify FAQ count is at least 15
        assert final_state.get('faq_page') is not None
        faq_count = len(final_state['faq_page'].faqs)
        assert faq_count >= 15, f"FAQ page must have at least 15 questions, got {faq_count}"
        
        print(f"\n✓ FAQ validation passed: {faq_count} questions generated")
    
    @pytest.mark.slow
    def test_question_generation_minimum(self, app, sample_product_data):
        """Test that question generator produces at least 15 questions."""
        initial_state = {
            "raw_data": sample_product_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        final_state = app.invoke(initial_state)
        
        questions = final_state.get('questions')
        assert questions is not None
        assert len(questions) >= 15, f"Must generate at least 15 questions, got {len(questions)}"
        
        # Verify category diversity
        categories = set(q.category for q in questions)
        assert len(categories) >= 3, f"Questions must cover at least 3 categories, got {len(categories)}"
        
        print(f"\n✓ Question generation validation passed:")
        print(f"  - Total questions: {len(questions)}")
        print(f"  - Categories: {categories}")
    
    @pytest.mark.slow
    def test_no_external_search_indicators(self, app, sample_product_data):
        """Test that generated content doesn't contain external search indicators."""
        initial_state = {
            "raw_data": sample_product_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        final_state = app.invoke(initial_state)
        
        # Check FAQ answers for external search indicators
        faq_page = final_state.get('faq_page')
        if faq_page:
            suspicious_phrases = [
                "according to search",
                "based on results",
                "found on website",
                "source: http"
            ]
            
            for idx, faq in enumerate(faq_page.faqs):
                answer_lower = faq.answer.lower()
                for phrase in suspicious_phrases:
                    assert phrase not in answer_lower, \
                        f"FAQ #{idx+1} contains external search indicator: '{phrase}'"
        
        print(f"\n✓ No external search indicators found")
    
    @pytest.mark.slow
    def test_self_correction_loop(self, app):
        """Test that self-correction loop works with minimal data."""
        # Provide minimal data that should trigger revisions
        minimal_data = {
            "name": "Test Product",
            "category": "Test",
            "price": 10.0,
            "currency": "USD",
            "description": "A test product with minimal description.",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "specs": {"size": "small"},
            "competitors": []
        }
        
        initial_state = {
            "raw_data": minimal_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        final_state = app.invoke(initial_state)
        
        # Check if revisions occurred
        revision_count = final_state.get('revision_count', 0)
        print(f"\n✓ Self-correction loop test completed")
        print(f"  - Revisions: {revision_count}")
        print(f"  - Final feedback: {final_state.get('review_feedback')}")
        
        # Even with minimal data, should eventually produce output or hit max retries
        assert revision_count <= 3, "Exceeded maximum retry limit"


class TestSchemaValidation:
    """Test schema validation with real LLM outputs."""
    
    @pytest.mark.slow
    def test_product_schema_validation(self, app, sample_product_data):
        """Test that ProductSchema validation works correctly."""
        initial_state = {
            "raw_data": sample_product_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        final_state = app.invoke(initial_state)
        clean_data = final_state.get('clean_data')
        
        assert clean_data is not None
        assert clean_data.price > 0
        assert len(clean_data.currency) == 3
        assert len(clean_data.features) >= 3
        assert len(clean_data.description) >= 50
        
        print(f"\n✓ ProductSchema validation passed")
    
    @pytest.mark.slow
    def test_faq_schema_validation(self, app, sample_product_data):
        """Test that FAQPageSchema validation works correctly."""
        initial_state = {
            "raw_data": sample_product_data,
            "revision_count": 0,
            "tone": "Professional"
        }
        
        final_state = app.invoke(initial_state)
        faq_page = final_state.get('faq_page')
        
        assert faq_page is not None
        assert len(faq_page.faqs) >= 15
        assert len(faq_page.title) >= 5
        assert len(faq_page.description) >= 10
        
        # Check individual FAQ quality
        for faq in faq_page.faqs:
            assert len(faq.question) >= 5
            assert len(faq.answer) >= 20  # Minimum quality threshold
        
        print(f"\n✓ FAQPageSchema validation passed")


class TestErrorHandling:
    """Test error handling and retry mechanisms."""
    
    @pytest.mark.slow
    def test_invalid_api_key_handling(self):
        """Test graceful handling of invalid API key."""
        # Temporarily override API key
        original_key = os.environ.get('GOOGLE_API_KEY')
        os.environ['GOOGLE_API_KEY'] = 'invalid_key_for_testing'
        
        try:
            app = create_graph()
            initial_state = {
                "raw_data": {"name": "Test"},
                "revision_count": 0,
                "tone": "Professional"
            }
            
            # Should fail gracefully, not crash
            with pytest.raises(Exception):
                app.invoke(initial_state)
        
        finally:
            # Restore original key
            if original_key:
                os.environ['GOOGLE_API_KEY'] = original_key
        
        print(f"\n✓ Invalid API key handled gracefully")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
