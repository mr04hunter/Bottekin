"""triggers

Revision ID: f11b9fd56113
Revises: 5e05589071f0
Create Date: 2026-05-09 11:57:23.125932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f11b9fd56113'
down_revision: Union[str, Sequence[str], None] = '5e05589071f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Vote Functions
    op.execute("""
        CREATE OR REPLACE FUNCTION increment_total_votes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.voter_id IS NOT NULL THEN
                UPDATE users SET times_voted = times_voted + 1 WHERE id = NEW.voter_id;
            END IF;
            UPDATE submissions SET total_votes = total_votes + 1 WHERE id = NEW.submission_id;
            UPDATE challenges SET total_votes = total_votes + 1 WHERE id = NEW.challenge_id;
            UPDATE users
            SET total_votes_received = total_votes_received + 1
            WHERE id = (
                SELECT author_id 
                FROM submissions 
                WHERE id = NEW.submission_id
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION decrement_total_votes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.voter_id IS NOT NULL THEN
                UPDATE users SET times_voted = times_voted - 1 WHERE id = OLD.voter_id;
            END IF;
            UPDATE submissions SET total_votes = total_votes - 1 WHERE id = OLD.submission_id;
            UPDATE challenges SET total_votes = total_votes - 1 WHERE id = OLD.challenge_id;
            UPDATE users
            SET total_votes_received = total_votes_received - 1
            WHERE id = (
                SELECT author_id 
                FROM submissions 
                WHERE id = OLD.submission_id
            );
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Feedback functions
    op.execute("""
        CREATE OR REPLACE FUNCTION increment_total_feedback()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_feedbacks_given = total_feedbacks_given + 1, total_feedback_words = total_feedback_words + NEW.word_count WHERE id = NEW.author_id;
            UPDATE tracks SET total_feedbacks = total_feedbacks + 1 WHERE id = NEW.track_id;
            UPDATE users
            SET total_feedbacks_received = total_feedbacks_received + 1
            WHERE id = (
                SELECT author_id 
                FROM tracks 
                WHERE id = NEW.track_id
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    
    op.execute("""
        CREATE OR REPLACE FUNCTION decrement_total_feedback()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_feedbacks_given = total_feedbacks_given - 1, total_feedback_words = total_feedback_words - OLD.word_count WHERE id = OLD.author_id;
            UPDATE tracks SET total_feedbacks = total_feedbacks - 1 WHERE id = OLD.track_id;
            UPDATE users
            SET total_feedbacks_received = total_feedbacks_received - 1
            WHERE id = (
                SELECT author_id 
                FROM tracks 
                WHERE id = OLD.track_id
            );
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION update_user_total_words()
    RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.word_count IS DISTINCT FROM OLD.word_count THEN
            UPDATE users 
            SET total_feedback_words = total_feedback_words + (NEW.word_count - OLD.word_count)
            WHERE id = NEW.author_id;
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
""")


    # Challenge functions

    op.execute("""
        CREATE OR REPLACE FUNCTION increment_total_submissions()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_submissions = total_submissions + 1 WHERE id = NEW.author_id;
            UPDATE challenges SET total_submissions = total_submissions + 1 WHERE id = NEW.challenge_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION decrement_total_submissions()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_submissions = total_submissions - 1 WHERE id = OLD.author_id;
            UPDATE challenges SET total_submissions = total_submissions - 1 WHERE id = OLD.challenge_id;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)


    op.execute("""
        CREATE OR REPLACE FUNCTION monthly_increment_total_submissions()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_submissions = total_submissions + 1 WHERE id = NEW.author_id;
            UPDATE monthly_challenges SET total_submissions = total_submissions + 1 WHERE id = NEW.challenge_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION monthly_decrement_total_submissions()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_submissions = total_submissions - 1 WHERE id = OLD.author_id;
            UPDATE monthly_challenges SET total_submissions = total_submissions - 1 WHERE id = OLD.challenge_id;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)




    op.execute("""
        CREATE OR REPLACE FUNCTION increment_total_wins()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_challenges_won = total_challenges_won + 1 WHERE id = NEW.winner_id;
            UPDATE submissions SET winner_declared = true WHERE id = NEW.submission_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION decrement_total_wins()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users SET total_challenges_won = total_challenges_won - 1 WHERE id = OLD.winner_id;
            UPDATE submissions SET winner_declared = false WHERE id = OLD.submission_id;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)



    # Create triggers
    op.execute("""
        CREATE TRIGGER vote_after_insert
        AFTER INSERT ON votes FOR EACH ROW
        EXECUTE FUNCTION increment_total_votes();
    """)
    
    op.execute("""
        CREATE TRIGGER vote_after_delete
        AFTER DELETE ON votes FOR EACH ROW
        EXECUTE FUNCTION decrement_total_votes();
    """)

    op.execute("""
        CREATE TRIGGER feedback_after_insert
        AFTER INSERT ON feedbacks FOR EACH ROW
        EXECUTE FUNCTION increment_total_feedback();
    """)
    
    op.execute("""
        CREATE TRIGGER feedback_after_delete
        AFTER DELETE ON feedbacks FOR EACH ROW
        EXECUTE FUNCTION decrement_total_feedback();
    """)

    op.execute("""
    CREATE TRIGGER feedback_after_update
    AFTER UPDATE ON feedbacks
    FOR EACH ROW
    EXECUTE FUNCTION update_user_total_words();
""")

    op.execute("""
        CREATE TRIGGER submission_after_insert
        AFTER INSERT ON submissions
        FOR EACH ROW
        EXECUTE FUNCTION increment_total_submissions()
    """)

    op.execute("""
        CREATE TRIGGER submission_after_delete
        AFTER DELETE ON submissions
        FOR EACH ROW
        EXECUTE FUNCTION decrement_total_submissions()
    """)


    op.execute("""
        CREATE TRIGGER monthly_submission_after_insert
        AFTER INSERT ON monthly_submissions
        FOR EACH ROW
        EXECUTE FUNCTION monthly_increment_total_submissions()
    """)

    op.execute("""
        CREATE TRIGGER monthly_submission_after_delete
        AFTER DELETE ON monthly_submissions
        FOR EACH ROW
        EXECUTE FUNCTION monthly_decrement_total_submissions()
    """)

    op.execute("""
        CREATE TRIGGER winner_after_insert
        AFTER INSERT ON winners
        FOR EACH ROW
        EXECUTE FUNCTION increment_total_wins()
    """)

    op.execute("""
        CREATE TRIGGER winner_after_delete
        AFTER DELETE ON winners
        FOR EACH ROW
        EXECUTE FUNCTION decrement_total_wins()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS submissions_after_delete ON submissions")
    op.execute("DROP TRIGGER IF EXISTS submissions_after_insert ON submissions")
    op.execute("DROP TRIGGER IF EXISTS vote_after_delete ON votes")
    op.execute("DROP TRIGGER IF EXISTS vote_after_insert ON votes")
    op.execute("DROP TRIGGER IF EXISTS winner_after_delete ON winners")
    op.execute("DROP TRIGGER IF EXISTS winner_after_insert ON winners")
    op.execute("DROP FUNCTION IF EXISTS decrement_total_votes()")
    op.execute("DROP FUNCTION IF EXISTS increment_total_votes()")
    op.execute("DROP TRIGGER IF EXISTS feedback_after_delete ON feedbacks")
    op.execute("DROP TRIGGER IF EXISTS feedback_after_insert ON feedbacks")
    op.execute("DROP TRIGGER IF EXISTS feedback_after_update ON feedbacks")
    op.execute("DROP FUNCTION IF EXISTS decrement_total_feedback()")
    op.execute("DROP FUNCTION IF EXISTS increment_total_feedback()")
    op.execute("DROP FUNCTION IF EXISTS update_user_total_words()")
    op.execute("DROP FUNCTION IF EXISTS increment_total_submissions()")
    op.execute("DROP FUNCTION IF EXISTS decrement_total_submissions()")
