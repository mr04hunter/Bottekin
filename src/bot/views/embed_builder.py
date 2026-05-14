from typing import Callable
from discord import Embed, Member, Colour
from discord import User as dc_user
from bot.database.models import Submission, User
import math
from bot.constants import (MUSIC_STATS_THUMBNAIL_URL,
                        FEEDBACK_STATS_THUMBNAIL_URL, 
                        CHALLENGE_STATS_THUMBNAIL_URL,
                        GENERIC_LEADERBOARD_THUMBNAIL_URL,
                        ALL_TIME_CHALLENGES_LEADERBOARD_THUMBNAIL_URL,
                        SUBMISSIONS_LEADERBOARD_THUMBNAIL_URL,
                        FEEDBACK_LEADERBOARD_THUMBNAIL_URL)
from bot.logging import get_logger

from datetime import timedelta
from bot.types import (AllTimeChallengeLeaderboardDisplay, BaseLeaderboardDisplay,
                        ChallengeLeaderboardDisplay, FeedbackLeaderboardDisplay, 
                        SubmissionLeaderboardDisplay, MusicStatsDisplay, FeedbackStatsDisplay,
                        ChallengeStatsDisplay, ServerActivityDisplay)
from bot.types.leaderboards.presentation import MostActiveMemberDisplay, MostActivePeriodDisplay


logger = get_logger("embed_builder")

LB_NOT_ENOUGH_DATA_TEXT = "\nNot enough data yet\nA leaderboard will be displayed here!"

class EmbedBuilder:
    """Embed builder class builds discord embeds and presents data"""

    
  
    def _get_rank(self, index:int) -> str:
        """returns the rank emoji of user"""
        emojis = {0:" :first_place: ", 1:" :second_place: ", 2:" :third_place: "}
        return emojis.get(index, " ")
    
    def _get_challenge_rank(self, index:int) -> str:
        """returns the rank of a user"""
        emojis = {0:" :first_place: ", 1:" :second_place: ", 2:" :third_place: "}
        return emojis.get(index, " ")
    

    def _get_possessive(self, display_name: str) -> str:
        """returns a possessive based on the value of display_name"""
        return "r" if display_name == "You" else "'s"
    

    def _get_mention_name(self, user: User, member: Member | dc_user | None) -> str:
        if member:
            return member.mention
        else:
            return user.display_name

    def _put_separator(self, length: int) -> str:
        """returns a seperator if the length is greater than 1
        this is usually used in leaderboards to seperate users from each other"""

        return "\n**────────────**\n" if length > 1 else ""

    def _check_plural(self, length: int) -> str:
        """returns plural suffix based on the given length"""

        return "s" if length > 1 else ""

    ########## STATS EMBEDS ##########


    def create_feedback_stats_embed(self, feedback_stats: FeedbackStatsDisplay, display_name: str) -> Embed:
        """returns an embed that presents the feedback stats data"""

        feedback_text = (f"{display_name} gave **{feedback_stats.total_feedbacks_given}** "
        f"feedback {"message" + self._check_plural(length=feedback_stats.total_feedbacks_given)}\n")
        if feedback_stats.total_members_given_feedback > 0:
            feedback_text += f"{display_name} gave feedback to **{feedback_stats.total_members_given_feedback}** members."

        feedback_embed = Embed(color=Colour.blue(), title="**FEEDBACK STATS**",description=feedback_text)
        
        feedback_embed.set_thumbnail(url=FEEDBACK_STATS_THUMBNAIL_URL)

        


        if feedback_stats.most_feedbacked_members:
            author_lines = []
            for author_name, count in feedback_stats.most_feedbacked_members: 

                text = (f"{display_name} gave **{count}** feedback "
                f"{"message" + self._check_plural(length=count)} to {author_name}"
                f"{self._put_separator(length=len(feedback_stats.most_feedbacked_members))}")
                author_lines.append(text)
                logger.bind(
                    author_mention=author_name,
                ).debug("Author & display name debug")
            
            most_feedbacked_authors_text = "".join(author_lines)

            feedback_embed.add_field(name=f"**TOP 3 MEMBERS {display_name.upper()} SUPPORTED THE MOST**", value=most_feedbacked_authors_text, inline=False)

        if feedback_stats.most_words_feedback_message:
            most_word_feedback, word_count = feedback_stats.most_words_feedback_message
            your_most_words_feedback_text = (f"{display_name}{self._get_possessive(display_name=display_name)} "
            f"longest feedback: {most_word_feedback.jump_url}\n Total words: **{word_count}**")
            feedback_embed.add_field(name="**FEEDBACK WITH THE MOST WORDS**", value=your_most_words_feedback_text, inline=False)

        return feedback_embed 
        

    def create_music_stats_embed(self, music_stats: MusicStatsDisplay, display_name: str) -> Embed | None:
        """returns an embed that presents the music stats data"""

        if music_stats.total_tracks == 0:
            return
        
        music_text = (f"{display_name} shared **{music_stats.total_tracks}** {"track" + self._check_plural(length=music_stats.total_tracks)} to get feedback\n"
                      f"Total feedback received: **{music_stats.total_feedback_received}**")

        
        music_embed = Embed(color=Colour.red(), title="**MUSIC STATS**",description=music_text) 
        music_embed.set_thumbnail(url=MUSIC_STATS_THUMBNAIL_URL) if music_embed else None

        most_words_feedback_text: str = "\n"
        top_tracks_stats_text: str | None =  "\n"
        top_stats_text = ""

        if music_stats.top_feedbacked_track_messages:
            top_tracks_stats_text = "".join([
                f"{track.jump_url} Total feedback received: **{total_feedback}**\n"
                for track, total_feedback in music_stats.top_feedbacked_track_messages if total_feedback > 0])
            
            if top_tracks_stats_text:
                music_embed.add_field(name="**TOP 3 TRACKS WITH MOST FEEDBACK:**", value=top_tracks_stats_text, inline=False)
        
        logger.debug(f"TOP FB TRACKS DONE")

        if music_stats.most_reacted_track_message:
            most_reacted_track_message, reaction_count = music_stats.most_reacted_track_message
            if reaction_count > 0:
                most_reacted_message_text = (f"{display_name}{self._get_possessive(display_name=display_name)} "
                f"most reacted track is {most_reacted_track_message.jump_url}\nIt received **{reaction_count}** reactions\n")
                
                music_embed.add_field(name="**MOST REACTED TRACK**",value=most_reacted_message_text)

        logger.debug(f"TOP MOST REACTED MESSAGE DONE")
           
        if music_stats.most_words_fb_received_message:
            most_words_fb_received_message, word_count = music_stats.most_words_fb_received_message
            if word_count > 0:
                mention_name = most_words_fb_received_message.author.mention

                if not most_words_fb_received_message.author.mention:
                    mention_name = most_words_fb_received_message.author.display_name

                most_words_feedback_text += (f"By: {mention_name}\nWord count: "
                f"**{word_count}**!\nMessage: {most_words_fb_received_message.jump_url}\n")

                music_embed.add_field(name="**FEEDBACK WITH THE MOST WORDS RECEIVED**", value=most_words_feedback_text, inline=False)


        logger.debug(f"MOST WORDS FB RECEIVED DONE")

        if music_stats.top_fb_givers:
            top_stats_lines = []
            for i, data in enumerate(music_stats.top_fb_givers):
                name, count = data
                emoji = self._get_rank(i)

                stat_text = (f"{emoji} {name} total feedback: "
                f"**{count}**{self._put_separator(length=len(music_stats.top_fb_givers))}")

                top_stats_lines.append(stat_text)
            
            top_stats_text = "".join(top_stats_lines)
            top_fb_givers_field_name = f"**{display_name.upper()}{self._get_possessive(display_name=display_name).upper()} TOP 3 FEEDBACK GIVERS**"
            music_embed.add_field(name=top_fb_givers_field_name, value=top_stats_text, inline=False)

        logger.debug(f"TOP TOP FB GIVERS DONE")
  
            
        logger.bind(
            music_text=music_text,
            music_embed=str(music_embed.to_dict()) if music_embed else None,
        ).debug("Return value of create_music_embed")

        return music_embed

    
    def create_challenge_stats_embed(self, challenge_stats:ChallengeStatsDisplay, display_name: str) -> Embed | None:
        """returns an embed that presents the challenge stats data"""
        if challenge_stats.total_submissions == 0:
            return
        
        description_text = (f"\n{display_name} participated in **{challenge_stats.total_submissions}** "
        f"{"challenge" + self._check_plural(length=challenge_stats.total_submissions)}\n")

        if challenge_stats.total_challenges_won != 0:
            description_text += (f"{display_name} won **{challenge_stats.total_challenges_won}** "
                                 f"{"challenge" + self._check_plural(length=challenge_stats.total_challenges_won)}\n")

        
        challenge_embed = Embed(
            color=Colour.orange(), 
            title="**CHALLENGE STATS**", 
            description=description_text
        )
        challenge_embed.set_thumbnail(url=CHALLENGE_STATS_THUMBNAIL_URL)
        
        

        return challenge_embed







    ########## BOARD EMBEDS ##########
    
    # Each leaderboard method has an inner function for their individual data formatting
    # Inner functions are passed as a callback function to the base leaderboard method


    def _create_leaderboard_base(self, title: str, description: str, leaderboard_data: BaseLeaderboardDisplay, entry_callback: Callable) -> Embed:
        leaderboard_embed = Embed(
            title=title,
            description=description,
            color=Colour.dark_purple()
        )
        if not leaderboard_data.data:
            leaderboard_embed.add_field(name="**LIVE LEADERBOARD**", value=LB_NOT_ENOUGH_DATA_TEXT,inline=False)
            return leaderboard_embed
        else:
            entries = [entry_callback(index, data) for index,data in enumerate(leaderboard_data.data)]

            leaderboard_embed.add_field(name="**LIVE LEADERBOARD**",
                                        value="".join(entries))
            
            return leaderboard_embed


    def create_challenge_leaderboard_embed(self, leaderboard_data: ChallengeLeaderboardDisplay) -> Embed:
        """returns an embed that presents the ongoing challenge leaderboard"""

        def data_entries(index: int, data: tuple[str, Submission]):
            rank = self._get_challenge_rank(index=index)
            member_name, submission = data
            return f"\n{index+1}.{rank}{member_name} total votes received: **{submission.total_votes}**.\n" 


        title = f"**{leaderboard_data.challenge_title.upper() if leaderboard_data else "CURRENT CHALLENGE"} LIVE LEADERBOARD**"
        description = (f"**CURRENT CHALLENGE STATS**\nTotal votes received in this challenge: "
            f"**{leaderboard_data.server_total_votes}**\nTotal submissions received in this challenge: "
            f"**{leaderboard_data.server_total_submissions}**\n")
        

        
        leaderboard_embed = self._create_leaderboard_base(title=title,description=description,
                                                          leaderboard_data=leaderboard_data, entry_callback=data_entries)
            
        
    
        leaderboard_embed.set_thumbnail(url=GENERIC_LEADERBOARD_THUMBNAIL_URL)

        return leaderboard_embed
    

    def create_all_time_challenges_won_leaderboards(self, leaderboard_data: AllTimeChallengeLeaderboardDisplay) -> Embed:
        """returns an embed that presents the all time challenge leaderboard"""


        def data_entries(index: int, data: tuple[str, int]):
            rank = self._get_challenge_rank(index=index)
            member_name, total_challenges_won = data
            return f"{index+1}.{rank}{member_name}\nTotal wins: **{total_challenges_won}**{self._put_separator(length=leaderboard_data.leaderboard_length)}"

        title = "**WINNERS LEADERBOARD**"
        description=(f"**SERVER STATS**\nTotal winners: "
            # f"**{len([total_challenges_won for data in leaderboard_data for member, total_challenges_won in data.items() if total_challenges_won != 0])}**\n")
            f"**{leaderboard_data.server_total_winners}**\n"
        )
       
        leaderboard_embed = self._create_leaderboard_base(title=title, description=description, 
                                                          leaderboard_data=leaderboard_data,entry_callback=data_entries)
        
        leaderboard_embed.set_thumbnail(url=ALL_TIME_CHALLENGES_LEADERBOARD_THUMBNAIL_URL)

 
        return leaderboard_embed
    




    def create_all_time_submissions_leaderboards(self, leaderboard_data: SubmissionLeaderboardDisplay) -> Embed:
        """returns an embed that presents the all time submissions leaderboard"""
        def data_entries(index: int, data: tuple[str, int]):
            rank = self._get_challenge_rank(index=index)
            member_name, submission_count = data
            return  f"{index+1}.{rank}{member_name}\nTotal submissions: **{submission_count}**{self._put_separator(length=leaderboard_data.leaderboard_length)}"

                
        title = "**MOST ACTIVE CHALLENGERS**" 
        description=(f"**SERVER STATS**\nTotal submissions: "
            f"**{leaderboard_data.server_total_submissions if leaderboard_data.server_total_submissions > 0 else "No data"}**\nTotal challenges: "
            f"**{leaderboard_data.server_total_challenges}**\n")
        
        
        leaderboard_embed = self._create_leaderboard_base(title=title, description=description, 
                                                          leaderboard_data=leaderboard_data, entry_callback=data_entries)        

        leaderboard_embed.set_thumbnail(url=SUBMISSIONS_LEADERBOARD_THUMBNAIL_URL)

        return leaderboard_embed





    def create_feedback_leaderboard(self, leaderboard_data: FeedbackLeaderboardDisplay) -> Embed:
        """returns an embed that presents the all time feedback leaderboard"""
        
        def data_entries(index:int, data:tuple[str, dict[str, int]]):
            rank = self._get_challenge_rank(index=index)
            member_name, feedback_data = data
            total_feedbacks_given = feedback_data.get("total_feedbacks_given",0)
            total_feedback_words = feedback_data.get("total_feedback_words",0)
            total_feedbacked_authors = feedback_data.get("total_feedbacked_authors",0)

            total_feedback_text = f"Total feedback: **{total_feedbacks_given}**\n" if total_feedbacks_given > 0 else ""
            total_fb_words_text = f"Total words: **{total_feedback_words}**\n" if total_feedback_words > 0 else ""
            total_feedbacked_authors_text = (f"Gave feedback to **{total_feedbacked_authors}** {"member" + self._check_plural(length=total_feedbacked_authors)}" 
                                             if total_feedbacked_authors > 0 else "") 

            return (f"{index+1}.{rank}{member_name}\n{total_feedback_text+total_fb_words_text+total_feedbacked_authors_text}"
                    f"{self._put_separator(leaderboard_data.leaderboard_length)}")

                
        total_tracks = leaderboard_data.server_total_tracks
        title = "**FEEDBACK LEADERBOARD**"



        description=(f"**SERVER STATS**\n"
            f"Feedback messages: "f"**{leaderboard_data.server_total_feedback if leaderboard_data.server_total_feedback >= 0 else "No data"}**\n"
            f"Total Tracks: "f"**{leaderboard_data.server_total_tracks if leaderboard_data.server_total_tracks >= 0 else "No data"}**\n"
            f"Total feedback words: **{leaderboard_data.server_total_fb_words if leaderboard_data.server_total_fb_words >= 0 else "No data"}**\n")


        leaderboard_embed = self._create_leaderboard_base(title=title, description=description, 
                                                          leaderboard_data=leaderboard_data, entry_callback=data_entries)

        leaderboard_embed.set_thumbnail(url=FEEDBACK_LEADERBOARD_THUMBNAIL_URL)

        return leaderboard_embed
    

    def create_server_activity_board(self, activity_data: ServerActivityDisplay) -> Embed:
        title = "**SERVER ACTIVITY**"
        description = "Daily/Weekly/monthly server activity"

        embed = Embed(
            title=title,
            description=description,
            color=Colour.dark_purple()
        )

        daily_activity_text = (f"Total **feedback** messages sent today: **{activity_data.today_activity.feedback_count}**"
                               f"\nTotal **tracks** shared today: **{activity_data.today_activity.track_count}**")
        
        week_activity_text = (f"Total **feedback** messages sent this week: **{activity_data.week_activity.feedback_count}**"
                               f"\nTotal **tracks** shared this week: **{activity_data.week_activity.track_count}**")
        
        month_activity_text = (f"Total **feedback** messages sent this month: **{activity_data.month_activity.feedback_count}**"
                               f"\nTotal **tracks** shared this month: **{activity_data.month_activity.track_count}**")

        embed.add_field(
            name="**DAILY ACTIVITY**",
            value=daily_activity_text,
            inline=False
        )

        embed.add_field(
            name="**WEEKLY ACTIVITY**",
            value=week_activity_text,
            inline=False
        )

        embed.add_field(
            name="**MONTHLY ACTIVITY**",
            value=month_activity_text,
            inline=False
        )

        return embed
    

    def create_most_active_periods_board(self, activity_data: MostActivePeriodDisplay, most_active_member_data: MostActiveMemberDisplay) -> Embed:
        title = "**MOST ACTIVE TIME PERIODS**"
        description = "Most active day/week/month"

        embed = Embed(
            title=title,
            description=description,
            color=Colour.dark_purple()
        )

        most_active_day_text = (f"The most active day is: {activity_data.day.date.strftime("%Y/%m/%d")}" 
                                f"\nTotal posts shared: **{activity_data.day.total}**"
                               f"\nTotal **feedback** messages sent: **{activity_data.day.total_feedback}**"
                               f"\nTotal **tracks** shared: **{activity_data.day.total_track}**")
        

        date = activity_data.week.date

        start_of_week = date - timedelta(days=date.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)        # Sunday
        most_active_week_text = (f"The most active week is: {f"{start_of_week.day}-{end_of_week.day}"} {activity_data.week.date.strftime("%Y %B")}" 
                                f"\nTotal posts shared: **{activity_data.week.total}**"
                               f"\nTotal **feedback** messages sent: **{activity_data.week.total_feedback}**"
                               f"\nTotal **tracks** shared: **{activity_data.week.total_track}**")
        
        most_active_month_text = (f"The most active month is: {activity_data.month.date.strftime("%Y %B")}" 
                                f"\nTotal posts shared: **{activity_data.month.total}**"
                               f"\nTotal **feedback** messages sent: **{activity_data.month.total_feedback}**"
                               f"\nTotal **tracks** shared: **{activity_data.month.total_track}**")



        most_active_member_text = (f"The most active member of all time: {most_active_member_data.member}"
                                   f"\nTotal **feedback** messages sent: **{most_active_member_data.total_feedback}**"
                                   f"\nTotal **tracks** shared: **{most_active_member_data.total_tracks}**"
                                   f"\nTotal posts: {most_active_member_data.total_feedback+most_active_member_data.total_tracks}"
                                   )


        embed.add_field(
            name="**MOST ACTIVE DAY**",
            value=most_active_day_text,
            inline=False
        )

        embed.add_field(
            name="**MOST ACTIVE WEEK**",
            value=most_active_week_text,
            inline=False
        )

        embed.add_field(
            name="**MOST ACTIVE MONTH**",
            value=most_active_month_text,
            inline=False
        )
        embed.add_field(
            name="**MOST ACTIVE MEMBER OF ALL TIME**",
            value=most_active_member_text,
            inline=False
        )

        return embed