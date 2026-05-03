from datetime import UTC, datetime, timedelta
from discord import Embed
import pytest
from unittest.mock import MagicMock
from bot.database.models import Challenge, Vote, Winner
from bot.utils.extract_attachment_data import MessageExtractor
from tests.factories.discord_factories import make_member, make_message, make_reaction

class TestExtractor:
    @pytest.fixture
    async def extractor(self, mock_bot, test_config, mock_track_extractor):
        return MessageExtractor(bot=mock_bot, config=test_config, track_extractor=mock_track_extractor)
    

    async def test_get_submission_title_attachment(self, extractor):
        message = make_message(attachments=[MagicMock(title="test_attachment_title")])
        title = await extractor.get_submission_title(message=message)
        
        assert title == "test_attachment_title"

        extractor.track_extractor.extract_title.assert_not_called()

    async def test_get_submission_title_url(self, extractor):
        message = make_message(content="http://test.com")
        title = await extractor.get_submission_title(message=message)
        
        assert title == "test_title"

        extractor.track_extractor.extract_title.assert_called_once_with("http://test.com")


    async def test_extract_time_data(self, extractor):
        content = "starts at: <t:1776838270> ends at: <t:1776924670>"

        data = extractor.extract_the_time_code(content=content)

        assert data.starts_at == datetime.fromtimestamp(timestamp=1776838270, tz=UTC)
        assert data.ends_at == datetime.fromtimestamp(timestamp=1776924670, tz=UTC)
        assert data.voting_ends_at == datetime.fromtimestamp(1776924670, tz=UTC) + timedelta(days=1)

    async def test_extract_time_data_case_sensitive(self, extractor):
        content = "stArtS aT: <t:1776838270> enDs at: <t:1776924670>"

        data = extractor.extract_the_time_code(content=content)

        assert data.starts_at == datetime.fromtimestamp(timestamp=1776838270, tz=UTC)
        assert data.ends_at == datetime.fromtimestamp(timestamp=1776924670, tz=UTC)
        assert data.voting_ends_at == datetime.fromtimestamp(1776924670, tz=UTC) + timedelta(days=1)

    async def test_extract_time_data_milliseconds(self, extractor):
        content = "starts at: <t:1776838270000> ends at: <t:1776924670000>"

        data = extractor.extract_the_time_code(content=content)

        assert data.starts_at == datetime.fromtimestamp(timestamp=1776838270, tz=UTC)
        assert data.ends_at == datetime.fromtimestamp(timestamp=1776924670, tz=UTC)
        assert data.voting_ends_at == datetime.fromtimestamp(1776924670, tz=UTC) + timedelta(days=1)

    async def test_extract_time_data_missing_date_returns_none(self, extractor):
        content = "starts at: <t:1776838270>"

        data = extractor.extract_the_time_code(content=content)

        assert data is None




    async def test_extract_embed_data(self, extractor):

        title = MagicMock(value="challenge1")
        title.name = "title:"
        task_description = MagicMock(value="some task description")
        task_description.name = "task description:"
        note = MagicMock(value="some note")
        note.name = "note:"
        duration = MagicMock(value="starts at: <t:1776838270> ends at: <t:1776924670>")
        duration.name = "challenge duration:"
        fields = [
            title, task_description,
            note, duration
            ]
        

        embed = MagicMock(spec=Embed, fields=fields)

        data = await extractor.extract_embed_data(message_id=11111, embed=embed)

        assert data is not None

        assert data.id == 11111
        assert data.title == "challenge1"
        assert data.description == "some task description"
        assert data.duration.starts_at == datetime.fromtimestamp(1776838270, tz=UTC)
        assert data.duration.ends_at == datetime.fromtimestamp(1776924670, tz=UTC)
        assert data.duration.voting_ends_at == datetime.fromtimestamp(1776924670, tz=UTC) + timedelta(days=1)

    
    async def test_extract_embed_data_case_sensitive(self, extractor):

        title = MagicMock(value="challenge1")
        title.name = "tiTlE:"
        task_description = MagicMock(value="some task description")
        task_description.name = "TaSk descriPtioN:"
        note = MagicMock(value="some note")
        note.name = "nOtE:"
        duration = MagicMock(value="starts at: <t:1776838270> ends at: <t:1776924670>")
        duration.name = "chAllEngE DuraTion:"
        fields = [
            title, task_description,
            note, duration
            ]
        

        embed = MagicMock(spec=Embed, fields=fields)

        data = await extractor.extract_embed_data(message_id=11111, embed=embed)

        assert data is not None

        assert data.id == 11111
        assert data.title == "challenge1"
        assert data.description == "some task description"
        assert data.duration.starts_at == datetime.fromtimestamp(1776838270, tz=UTC)
        assert data.duration.ends_at == datetime.fromtimestamp(1776924670, tz=UTC)
        assert data.duration.voting_ends_at == datetime.fromtimestamp(1776924670, tz=UTC) + timedelta(days=1)


    async def test_extract_embed_data_no_title(self, extractor):

 
            task_description = MagicMock(value="some task description")
            task_description.name = "task description:"
            note = MagicMock(value="some note")
            note.name = "note:"
            duration = MagicMock(value="starts at: <t:1776838270> ends at: <t:1776924670>")
            duration.name = "challenge duration:"
            fields = [
                task_description,
                note, duration
                ]
            

            embed = MagicMock(spec=Embed, fields=fields)

            data = await extractor.extract_embed_data(message_id=11111, embed=embed)

            assert data is None

            
    
    async def test_extract_embed_data_no_description(self, extractor):

        title = MagicMock(value="challenge1")
        title.name = "title:"
        note = MagicMock(value="some note")
        note.name = "note:"
        duration = MagicMock(value="starts at: <t:1776838270> ends at: <t:1776924670>")
        duration.name = "challenge duration:"
        fields = [
            title,
            note, duration
            ]
        

        embed = MagicMock(spec=Embed, fields=fields)

        data = await extractor.extract_embed_data(message_id=11111, embed=embed)

        assert data is not None

        assert data.id == 11111
        assert data.title == "challenge1"
        assert data.description == "unknown description"
        assert data.duration.starts_at == datetime.fromtimestamp(1776838270, tz=UTC)
        assert data.duration.ends_at == datetime.fromtimestamp(1776924670, tz=UTC)
        assert data.duration.voting_ends_at == datetime.fromtimestamp(1776924670, tz=UTC) + timedelta(days=1)



    async def test_extract_embed_data_no_duration(self, extractor):

        title = MagicMock(value="challenge1")
        title.name = "title:"
        task_description = MagicMock(value="some task description")
        task_description.name = "task description:"
        note = MagicMock(value="some note")
        note.name = "note:"
    
        fields = [
            title, task_description,
            note
            ]
        

        embed = MagicMock(spec=Embed, fields=fields)

        data = await extractor.extract_embed_data(message_id=11111, embed=embed)

        assert data is None





    async def test_extract_track_message_title_url(self, extractor, test_config):
        channel = MagicMock(id=test_config.feedback_link_channel_ids[0])
        message = make_message(content="http://test.com")
        message.channel = channel

        title, platform = await extractor.extract_track_message_title(message=message)

        assert title == "test_title"
        assert platform == "test_platform"


    async def test_extract_track_message_title_attachment(self, extractor, test_config):
        channel = MagicMock(id=test_config.feedback_attachment_channel_ids[0])
        message = make_message(content="test_content", attachments=[MagicMock(title="test_attachment_title", content_type="audio/mpeg")])
        message.channel = channel

        title, platform = await extractor.extract_track_message_title(message=message)

        assert title == "test_attachment_title"
        assert platform == "attachment"

    async def test_extract_track_message_title_unrelated_channel_returns_none(self, extractor, test_config):
        channel = MagicMock(id=23423)
        message = make_message(content="test_content", attachments=[MagicMock(title="test_attachment_title", content_type="audio/mpeg")])
        message.channel = channel

        assert await extractor.extract_track_message_title(message=message) is None

    async def test_extract_track_message_title_no_attachment(self, extractor, test_config):
        channel = MagicMock(id=test_config.feedback_attachment_channel_ids[0])
        message = make_message(content="test_content", attachments=[])
        message.channel = channel

        assert await extractor.extract_track_message_title(message=message) is None

    async def test_extract_track_message_title_no_url(self, extractor, test_config):
        channel = MagicMock(id=test_config.feedback_link_channel_ids[0])
        message = make_message(content="test_content", attachments=[])
        message.channel = channel

        assert await extractor.extract_track_message_title(message=message) is None


    async def test_collect_votes(self, extractor):
        author = make_member(id=123456)
        voter1 = make_member(id=1234567)
        voter2 = make_member(id=12345678)
        voter3 = make_member(id=123456789)

        existing_user_ids = {author.id, voter1.id, voter2.id, voter3.id}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(users=[voter1, voter2, voter3])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        votes = await extractor.collect_votes(
            reaction_emojis={
                "👍":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            votes={}
        )

        assert len(votes) == 3
        vote_voter1 = votes[voter1.id]
        assert vote_voter1.submission_id == submission_message.id
        assert vote_voter1.voter_id == voter1.id
        assert vote_voter1.challenge_id == challenge.id

        vote_voter2 = votes[voter2.id]
        assert vote_voter2.submission_id == submission_message.id
        assert vote_voter2.voter_id == voter2.id
        assert vote_voter2.challenge_id == challenge.id

        vote_voter3 = votes[voter3.id]
        assert vote_voter3.submission_id == submission_message.id
        assert vote_voter3.voter_id == voter3.id
        assert vote_voter3.challenge_id == challenge.id


    async def test_collect_votes_unrelated_emoji_not_counted(self, extractor):
        author = make_member(id=123456)
        voter1 = make_member(id=1234567)
        voter2 = make_member(id=12345678)
        voter3 = make_member(id=123456789)
        voter4 = make_member(id=123456789)

        existing_user_ids = {author.id, voter1.id, voter2.id, voter3.id, voter4.id}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(users=[voter1, voter2, voter3])
        unrelated_reaction = make_reaction(emoji="🖤", users=[voter4])
        submission_message.reactions = [reaction, unrelated_reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        votes = await extractor.collect_votes(
            reaction_emojis={
                "👍":reaction,
                "🖤":unrelated_reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            votes={}
        )

        assert len(votes) == 3
        vote_voter1 = votes[voter1.id]
        assert vote_voter1.submission_id == submission_message.id
        assert vote_voter1.voter_id == voter1.id
        assert vote_voter1.challenge_id == challenge.id

        vote_voter2 = votes[voter2.id]
        assert vote_voter2.submission_id == submission_message.id
        assert vote_voter2.voter_id == voter2.id
        assert vote_voter2.challenge_id == challenge.id

        vote_voter3 = votes[voter3.id]
        assert vote_voter3.submission_id == submission_message.id
        assert vote_voter3.voter_id == voter3.id
        assert vote_voter3.challenge_id == challenge.id


    async def test_collect_votes_nonexistent_user(self, extractor):
        author = make_member(id=123456)
        voter1 = make_member(id=1234567)
        voter2 = make_member(id=12345678)
        voter3 = make_member(id=123456789)

        existing_user_ids = {author.id, voter1.id, voter2.id}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(users=[voter1, voter2, voter3])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        votes = await extractor.collect_votes(
            reaction_emojis={
                "👍":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            votes={}
        )

        assert len(votes) == 2
        vote_voter1 = votes[voter1.id]
        assert vote_voter1.submission_id == submission_message.id
        assert vote_voter1.voter_id == voter1.id
        assert vote_voter1.challenge_id == challenge.id

        vote_voter2 = votes[voter2.id]
        assert vote_voter2.submission_id == submission_message.id
        assert vote_voter2.voter_id == voter2.id
        assert vote_voter2.challenge_id == challenge.id

        vote_voter3 = votes.get(voter3.id)
        assert vote_voter3 is None


    async def test_collect_votes_update(self, extractor):
        author = make_member(id=123456)
        author2 = make_member(id=123456456)
        voter1 = make_member(id=1234567)
        voter2 = make_member(id=12345678)
        voter3 = make_member(id=123456789)



        existing_user_ids = {author.id, voter1.id, voter2.id, voter3.id}
        submission_message = make_message(id=12345, author=author)
        submission_message_updated = make_message(id=1234565756, author=author2)
        reaction = make_reaction(users=[voter1, voter2, voter3])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)

        current_votes = {
            voter1.id:MagicMock(spec=Vote, voter_id=voter1.id, submission_id=submission_message.id, challenge_id=challenge.id),
            voter2.id:MagicMock(spec=Vote, voter_id=voter2.id, submission_id=submission_message.id, challenge_id=challenge.id),
            voter3.id:MagicMock(spec=Vote, voter_id=voter3.id, submission_id=submission_message.id, challenge_id=challenge.id)}
        votes = await extractor.collect_votes(
            reaction_emojis={
                "👍":reaction
            },
            message=submission_message_updated,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            votes=current_votes
        )

        assert len(votes) == 3
        vote_voter1 = votes[voter1.id]
        assert vote_voter1.submission_id == submission_message_updated.id
        assert vote_voter1.voter_id == voter1.id
        assert vote_voter1.challenge_id == challenge.id

        vote_voter2 = votes[voter2.id]
        assert vote_voter2.submission_id == submission_message_updated.id
        assert vote_voter2.voter_id == voter2.id
        assert vote_voter2.challenge_id == challenge.id

        vote_voter3 = votes[voter3.id]
        assert vote_voter3.submission_id == submission_message_updated.id
        assert vote_voter3.voter_id == voter3.id
        assert vote_voter3.challenge_id == challenge.id


    async def test_collect_votes_update_previous_votes_remain(self, extractor):
        author = make_member(id=123456)
        author2 = make_member(id=123456456)
        voter1 = make_member(id=1234567)
        voter2 = make_member(id=12345678)
        voter3 = make_member(id=123456789)



        existing_user_ids = {author.id, voter1.id, voter2.id, voter3.id}
        submission_message = make_message(id=12345, author=author)
        submission_message_updated = make_message(id=1234565756, author=author2)
        reaction = make_reaction(users=[voter1, voter2, voter3])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)

        current_votes = {
            voter1.id:MagicMock(spec=Vote, voter_id=voter1.id, submission_id=submission_message.id, challenge_id=challenge.id),
            voter2.id:MagicMock(spec=Vote, voter_id=voter2.id, submission_id=submission_message.id, challenge_id=challenge.id),
            voter3.id:MagicMock(spec=Vote, voter_id=voter3.id, submission_id=submission_message.id, challenge_id=challenge.id)}
        votes = await extractor.collect_votes(
            reaction_emojis={},
            message=submission_message_updated,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            votes=current_votes
        )

        assert len(votes) == 3
        vote_voter1 = votes[voter1.id]
        assert vote_voter1.submission_id == submission_message.id
        assert vote_voter1.voter_id == voter1.id
        assert vote_voter1.challenge_id == challenge.id

        vote_voter2 = votes[voter2.id]
        assert vote_voter2.submission_id == submission_message.id
        assert vote_voter2.voter_id == voter2.id
        assert vote_voter2.challenge_id == challenge.id

        vote_voter3 = votes[voter3.id]
        assert vote_voter3.submission_id == submission_message.id
        assert vote_voter3.voter_id == voter3.id
        assert vote_voter3.challenge_id == challenge.id



    async def test_collect_votes_author_votes(self, extractor):
        """ Authors cant vote for their own submissions """
        author = make_member(id=123456)
        voter1 = make_member(id=1234567)
        voter2 = make_member(id=12345678)
        voter3 = make_member(id=123456789)

        existing_user_ids = {author.id, voter1.id, voter2.id, voter3.id}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(users=[voter1, voter2, voter3, author])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        votes = await extractor.collect_votes(
            reaction_emojis={
                "👍":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            votes={}
        )

        assert len(votes) == 3
        vote_voter1 = votes[voter1.id]
        assert vote_voter1.submission_id == submission_message.id
        assert vote_voter1.voter_id == voter1.id
        assert vote_voter1.challenge_id == challenge.id

        vote_voter2 = votes[voter2.id]
        assert vote_voter2.submission_id == submission_message.id
        assert vote_voter2.voter_id == voter2.id
        assert vote_voter2.challenge_id == challenge.id

        vote_voter3 = votes[voter3.id]
        assert vote_voter3.submission_id == submission_message.id
        assert vote_voter3.voter_id == voter3.id
        assert vote_voter3.challenge_id == challenge.id

        vote_author = votes.get(author.id)
        assert vote_author is None


    async def test_collect_winners(self, extractor, test_config):
        author = make_member(id=123456)
        admin = make_member(id=test_config.admin_id)
        voter1 = make_member(id=1234567)

        existing_user_ids = {author.id, voter1.id, admin}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(emoji="🏆" ,users=[admin])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        winners = await extractor.get_winner_data(
            reaction_emojis={
                "🏆":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            winners=set()
        )

        assert len(winners) == 1
        winners = list(winners)
        assert winners[0].winner_id == submission_message.author.id
        assert winners[0].submission_id == submission_message.id
        assert winners[0].challenge_id == challenge.id


    async def test_collect_winners_remain(self, extractor, test_config):
        author = make_member(id=123456)
        admin = make_member(id=test_config.admin_id)
        voter1 = make_member(id=1234567)

    
        existing_user_ids = {author.id, voter1.id, admin}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(emoji="🏆" ,users=[admin])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)

        current_winners = {MagicMock(spec=Winner, winner_id=12345678656, submission_id=12432435, challenge_id=challenge.id)}

        winners = await extractor.get_winner_data(
            reaction_emojis={
                "🏆":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            winners=current_winners
        )

        assert len(winners) == 2
        winners = {winner.winner_id:winner for winner in winners}
        
        winner1 = winners.get(submission_message.author.id)
        assert winner1 is not None
        assert winner1.winner_id == submission_message.author.id
        assert winner1.submission_id == submission_message.id
        assert winner1.challenge_id == challenge.id

        winner2 = winners.get(12345678656)
        assert winner2 is not None
        assert winner2.winner_id == 12345678656
        assert winner2.submission_id == 12432435
        assert winner2.challenge_id == challenge.id



    async def test_collect_winners_unprivileged(self, extractor):
        author = make_member(id=123456)
        admin = make_member(id=123456) #non admin user
        voter1 = make_member(id=1234567)

        existing_user_ids = {author.id, voter1.id, admin}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(emoji="🏆" ,users=[admin])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        winners = await extractor.get_winner_data(
            reaction_emojis={
                "🏆":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            winners=set()
        )

        assert len(winners) == 0


    
    async def test_collect_winners_nonexistent_author(self, extractor, test_config):
        author = make_member(id=123456)
        admin = make_member(id=test_config.admin_id) #non admin user
        voter1 = make_member(id=1234567)

        existing_user_ids = {voter1.id, admin}
        submission_message = make_message(id=12345, author=author)
        reaction = make_reaction(emoji="🏆" ,users=[admin])
        submission_message.reactions = [reaction]
        challenge = MagicMock(id=111, spec=Challenge)
        winners = await extractor.get_winner_data(
            reaction_emojis={
                "🏆":reaction
            },
            message=submission_message,
            existing_user_ids=existing_user_ids,
            challenge=challenge,
            winners=set()
        )

        assert len(winners) == 0


    async def test_get_attachment_title_mp(self, extractor):
        attachment = MagicMock(title=None, filename="test_song.mp3")

        title = extractor.get_title(attachment=attachment)

        assert title == "testsong"

    
    async def test_get_attachment_title_wav(self, extractor):
        attachment = MagicMock(title=None, filename="test_song.wav")

        title = extractor.get_title(attachment=attachment)

        assert title == "testsong"