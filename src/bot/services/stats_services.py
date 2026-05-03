from collections import Counter
import discord
from discord import Client, Embed, Guild, Thread, TextChannel
from bot.database.models import  User
from bot.database.unit_of_work import UnitOfWork
from bot.types import FeedbackStatsData, MusicStatsData, ChallengeStatsData
from bot.logging import get_logger
from bot.types.stats.presentation import MusicStatsDisplay, FeedbackStatsDisplay, ChallengeStatsDisplay
from typing import TYPE_CHECKING, cast
from bot.views.embed_builder import EmbedBuilder
from bot.stats.music import make_music_stats
from bot.stats.feedback import make_feedback_stats
from bot.stats.challenge import make_challenge_stats
import traceback as tb
from bot.services.base_service import BaseService

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.utils.converters import BotConverter
logger = get_logger("stats_service")

class StatsService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: "ChannelProvider", converter:"BotConverter") -> None:
        super().__init__(uow=uow, bot=bot)
        self.embed_builder = EmbedBuilder()
        self.converter = converter

   
    async def fetch_music_stats(self, guild: Guild, user: User, display_name: str) -> Embed | None:

            if not user.tracks:
                return

            try:
                logger.debug("track stats init")
                music_stats = make_music_stats(user)
                music_display_data = MusicStatsDisplay(total_tracks=music_stats.total_tracks, total_feedback_received=user.total_feedbacks_received)
                if music_stats.top_fb_givers:
                    try:
                        top_feedbacked_members = await self.converter.convert_users_to_members_data(data=music_stats.top_fb_givers)
                        music_display_data.top_fb_givers = top_feedbacked_members
                    except Exception as e:
                        logger.bind(
                            error=str(e)
                        ).warning(f"Could not convert top_feedbacked_members data")
                        
                if music_stats.most_words_received_feedback:
                    try:
                        thread = await guild.fetch_channel(music_stats.most_words_received_feedback.thread_id)
                        thread = cast(Thread, thread)
                        most_words_feedback_message = await thread.fetch_message(music_stats.most_words_received_feedback.id)
                        music_display_data.most_words_fb_received_message = (most_words_feedback_message, music_stats.most_words_received_feedback.word_count)

                    except discord.NotFound:
                        logger.bind(
                            most_words_feedback_id=str(music_stats.most_words_received_feedback.id)
                        ).warning(f"Could not fetch most_words_received feedback message")

                if music_stats.most_reacted_track:
                    try:
                        channel = await guild.fetch_channel(music_stats.most_reacted_track.channel_id)
                        channel = cast(TextChannel, channel)
                        most_reacted_track_message = await channel.fetch_message(music_stats.most_reacted_track.id)
                        music_display_data.most_reacted_track_message = (most_reacted_track_message,music_stats.most_reacted_track.total_reactions)
                    except discord.NotFound:
                        logger.bind(
                            most_reacted_track_id=str(music_stats.most_reacted_track.id)
                        ).warning(f"Could not fetch most_reacted_track message")
                
                top_feedbacked_track_messages = []
                if music_stats.top_feedbacked_tracks:
                    for track in music_stats.top_feedbacked_tracks:
                        try:
                            channel = await guild.fetch_channel(track.channel_id)
                            channel = cast(TextChannel, channel)
                            track_message = await channel.fetch_message(track.id)
                            top_feedbacked_track_messages.append((track_message, track.total_feedbacks))
                        except discord.NotFound:
                            logger.bind(
                                track_id=str(track.id)
                            ).warning(f"Could not fetch top_feedback_track")

                music_display_data.top_feedbacked_track_messages = top_feedbacked_track_messages
                music_embed = self.embed_builder.create_music_stats_embed(music_stats=music_display_data, display_name=display_name)
                logger.bind(
                    music_embed=music_embed 
                ).debug("Music embed")
                return music_embed
            except discord.NotFound as e:
                logger.bind(
                    response=e.response,
                    error=str(e),
                    traceback=tb.format_exc()
                ).warning("Failed to build music embed, error retrieving message/channel/member data from discord api")

            except Exception as e:
                logger.bind(
                    error=str(e),
                    traceback=tb.format_exc()
                ).error("Failed to build music embed") 


    async def fetch_feedback_stats(self, guild: Guild, user: User, client: Client, display_name:str) -> Embed | None:
        if not user.total_feedbacks_given:
            return
        try:
            logger.debug("feedback stats init")
            feedback_stats = make_feedback_stats(user)
            
            feedback_display_data = FeedbackStatsDisplay(total_feedback_word_count=feedback_stats.total_feedback_word_count,
                                                            total_feedbacks_given=feedback_stats.total_feedbacks_given)
            




            most_feedbacked_members = []
            for author, count in feedback_stats.most_feedbacked_authors:
                try:
                    
                    member = await client.fetch_user(author.id)
                    most_feedbacked_members.append((member.mention, count))

                except discord.NotFound:
                    most_feedbacked_members.append((author.display_name, count))
                    logger.bind(
                        user_id=author.id
                    ).warning("User could not fetched")
            feedback_display_data.most_feedbacked_members = most_feedbacked_members
            

            

            if feedback_stats.most_words_feedback:
                try:
                    thread = await guild.fetch_channel(feedback_stats.most_words_feedback.thread_id)
                    thread = cast(Thread, thread)
                    dc_most_words_feedback_message = await thread.fetch_message(feedback_stats.most_words_feedback.id)
                    feedback_display_data.most_words_feedback_message = (dc_most_words_feedback_message, feedback_stats.most_words_feedback.word_count)
                except discord.NotFound:
                    logger.bind(
                        message_id=feedback_stats.most_words_feedback.id
                    ).warning("Error fetching feedback message")



            feedback_embed = self.embed_builder.create_feedback_stats_embed(feedback_stats=feedback_display_data, display_name=display_name)
            logger.bind(
                feedback_embed=feedback_embed
            ).debug("Feedback embed")

            return feedback_embed
        except discord.NotFound as e:
            logger.bind(
                response=e.response,
                error=str(e),
                traceback=tb.format_exc()

            ).warning("Failed to build feedback embed, Error while fetching data from discord api")

        except Exception as e:
            logger.bind(
                error=str(e),
                traceback=tb.format_exc()
            ).error("Failed to build feedback embed") 



    async def fetch_challenge_stats(self, guild: Guild, user: User, client: Client, display_name:str) -> Embed | None:
        if not user.total_submissions > 0:
            return

                
        challenge_stats = make_challenge_stats(stats=user)
        
        challenge_display_data = ChallengeStatsDisplay(
                                most_voted_submissions=challenge_stats.most_voted_submissions,
                                total_votes_received=challenge_stats.total_votes_received,
                                total_submissions=challenge_stats.total_submissions,
                                total_challenges_won=challenge_stats.total_challenges_won,
                                times_voted=challenge_stats.times_voted)


        if challenge_stats.most_votes_received_by_user:
            
            most_votes_received_user, most_votes_received_count = challenge_stats.most_votes_received_by_user

            try:
                
                dc_most_received_vote_member = await client.fetch_user(most_votes_received_user.id)
                mention_val = dc_most_received_vote_member.mention
                
                challenge_display_data.most_votes_received_by_member = (mention_val, most_votes_received_count)

            except discord.NotFound:
                logger.bind(
                    user_id=most_votes_received_user.id 
                ).warning("Member Could not found")

                challenge_display_data.most_votes_received_by_member = (most_votes_received_user.display_name, most_votes_received_count)

        if challenge_stats.most_voted_user:
            most_voted_user, most_vote_count = challenge_stats.most_voted_user
            try:
                dc_most_voted_member = await client.fetch_user(most_voted_user.id)
                mention_val = dc_most_voted_member.mention
                challenge_display_data.most_voted_member = (mention_val, most_vote_count)

            except discord.NotFound:
                logger.bind( 
                    user_id=most_voted_user.id
                ).warning("Member Could not found")
                challenge_display_data.most_voted_member = (most_voted_user.display_name, most_vote_count)



        challenge_embed = self.embed_builder.create_challenge_stats_embed(challenge_stats=challenge_display_data, display_name=display_name)
        return challenge_embed




