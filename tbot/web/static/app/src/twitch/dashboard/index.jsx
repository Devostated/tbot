import React from 'react'
import {Route, Redirect} from "react-router-dom"
import {requireAuth} from 'tbot/twitch/utils'
import {renderError} from 'tbot/utils'
import api from 'tbot/twitch/api'
import Loading from 'tbot/components/loading'
import Sidebar from './components/sidebar'
import Topbar from './components/topbar'
import Dashboard from './dashboard'
import Commands from './commands'
import Command from './command'
import Spotify from './spotify'
import Discord from './discord'
import Admins from './admins'

class Main extends React.Component {

    render() {
        if (!this.props.match.params.channel) 
            return <Redirect to={`/twitch/${window.tbot.twitch_user.user}/dashboard`} />
        if (this.state.loading) {
            this.getChannel()
            return <Loading text="LOADING" />
        }
        if (this.state.error) {
            return <div className="mt-5 ml-auto mr-auto" style={{width: '600px'}}>
                {renderError(this.state.error)}
            </div>
        }
        return <div id="main-wrapper">
            <Sidebar />
            <div id="content-wrapper">
                <Topbar />
                <div id="content">
                    <Route exact path='/twitch/:channel/dashboard' component={Dashboard}/>
                    <Route exact path='/twitch/:channel/commands' component={Commands}/>
                    <Route exact path='/twitch/:channel/commands/edit/:id' component={Command}/>
                    <Route exact path='/twitch/:channel/commands/new' component={Command}/>
                    <Route exact path='/twitch/:channel/spotify' component={Spotify}/>
                    <Route exact path='/twitch/:channel/discord' component={Discord}/>
                    <Route exact path='/twitch/:channel/admins' component={Admins}/>
                </div>
            </div>
        </div>
    }

    constructor(props) {
        super(props)
        requireAuth()
        this.state = {
            loading: true,
            errors: null,
        }
    }

    componentDidUpdate(prevProps) {
        if (this.props.location !== prevProps.location) {
            window.scrollTo(0, 0)
        }
    }

    getChannel() {
        window.managedUser = null
        api.get(`/api/twitch/channel/${this.props.match.params.channel}`).then(r => {
            window.managedUser = r.data
            this.setState({loading: false})
        }).catch(e => {
            this.setState({loading: false, error: e.response.data})
        })
    }

}

export default Main